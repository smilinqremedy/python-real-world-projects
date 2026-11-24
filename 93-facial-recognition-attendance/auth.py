"""
Authentication, Password Security, and Role-Based Access Control (RBAC).
Uses PBKDF2-HMAC-SHA256 with cryptographically random salts.
"""
import hashlib
import os
import secrets
from typing import Tuple, Optional


def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
    """
    Hashes a password with PBKDF2-HMAC-SHA256 (100,000 iterations).
    Returns (hex_hash, hex_salt).
    """
    if salt is None:
        salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return key.hex(), salt.hex()


def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    """Verifies a plaintext password against the stored salt and hash using constant-time comparison."""
    try:
        salt_bytes = bytes.fromhex(stored_salt)
        calc_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 100000).hex()
        return secrets.compare_digest(calc_hash, stored_hash)
    except Exception:
        return False
