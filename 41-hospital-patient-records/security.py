"""
Security, Role-Based Access Control (RBAC), password hashing, and log sanitization.
"""
import hashlib
import hmac
import os
import re

# ==================== Password Hashing & Verification ====================

def generate_salt(length: int = 16) -> str:
    """Generate a cryptographically secure random hexadecimal salt."""
    return os.urandom(length).hex()


def hash_password(password: str, salt: str = None, iterations: int = 10_000) -> tuple[str, str]:
    """
    Hash a plaintext password using PBKDF2-HMAC-SHA256.
    Returns (password_hash, salt).
    """
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    if salt is None:
        salt = generate_salt()
    pwd_bytes = password.encode("utf-8")
    salt_bytes = bytes.fromhex(salt)
    derived = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, iterations)
    return derived.hex(), salt


def verify_password(password: str, salt: str, expected_hash: str, iterations: int = 10_000) -> bool:
    """Safely verify password match using constant-time comparison."""
    if not password or not salt or not expected_hash:
        return False
    computed_hash, _ = hash_password(password, salt, iterations=iterations)
    return hmac.compare_digest(computed_hash, expected_hash)


# ==================== Role-Based Access Control (RBAC) ====================

# Granular permission definitions
PERMISSIONS = {
    "admin": {
        "patient:create",
        "patient:view_demographics",
        "patient:view_clinical",
        "patient:update",
        "appointment:create",
        "appointment:view",
        "appointment:update",
        "visit:create",
        "visit:view",
        "vitals:create",
        "vitals:view",
        "clinical_notes:create",
        "clinical_notes:view",
        "billing:create",
        "billing:view",
        "user:manage",
        "reports:view",
        "audit:view",
    },
    "doctor": {
        "patient:view_demographics",
        "patient:view_clinical",
        "patient:update",
        "appointment:view",
        "appointment:update",
        "visit:create",
        "visit:view",
        "vitals:create",
        "vitals:view",
        "clinical_notes:create",
        "clinical_notes:view",
        "reports:view",
    },
    "nurse": {
        "patient:view_demographics",
        "patient:view_clinical",
        "appointment:view",
        "visit:create",
        "visit:view",
        "vitals:create",
        "vitals:view",
        "clinical_notes:view",  # View only; nursing progress notes can be added via consultation notes if permitted
    },
    "receptionist": {
        "patient:create",
        "patient:view_demographics",
        "patient:update",
        "appointment:create",
        "appointment:view",
        "appointment:update",
        "visit:create",
        "visit:view",
    },
    "billing": {
        "patient:view_demographics",
        "visit:view",
        "billing:create",
        "billing:view",
        "reports:view",
    },
}


class AccessDeniedError(PermissionError):
    """Raised when an operation violates Role-Based Access Control."""
    pass


def check_permission(user_role: str, required_permission: str) -> bool:
    """Check if the given role has the requested permission."""
    allowed = PERMISSIONS.get(user_role.lower(), set())
    return required_permission in allowed


def require_permission(user: dict, required_permission: str) -> None:
    """Enforce permission check for the authenticated user context."""
    if not user:
        raise AccessDeniedError("Authentication required. No active user context.")
    role = user.get("role", "").lower()
    if not check_permission(role, required_permission):
        username = user.get("username", "Unknown")
        raise AccessDeniedError(
            f"Access denied: User '{username}' with role '{role}' lacks '{required_permission}' permission."
        )


# ==================== Log Sanitization & Privacy Protection ====================

def mask_phone(phone: str) -> str:
    """Mask phone number for safe display and logging (e.g., +234-***-***-1234)."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) <= 4:
        return "****"
    return f"***-***-{digits[-4:]}"


def mask_email(email: str) -> str:
    """Mask email address for privacy (e.g., j***e@domain.com)."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def mask_name(name: str) -> str:
    """Mask patient full name for anonymous logs (e.g., J*** D**)."""
    if not name:
        return ""
    parts = name.strip().split()
    masked_parts = []
    for part in parts:
        if len(part) <= 1:
            masked_parts.append(part)
        else:
            masked_parts.append(part[0] + "*" * (len(part) - 1))
    return " ".join(masked_parts)


def sanitize_for_audit(details: str) -> str:
    """
    Remove potentially sensitive clinical content, passwords, or PII from audit details.
    """
    if not details:
        return ""
    # Strip potential password strings
    sanitized = re.sub(r"(password|pwd|secret)=['\"]?[^'\"\s]+['\"]?", r"\1=[REDACTED]", details, flags=re.I)
    # Strip phone numbers
    sanitized = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE_REDACTED]", sanitized)
    # Strip email addresses
    sanitized = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_REDACTED]", sanitized)
    return sanitized
