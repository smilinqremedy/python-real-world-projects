"""
Local, privacy-preserving Password Security Audit Tool.
Zero persistence, zero external network transmission.
"""
from dataclasses import dataclass
import math
import re

COMMON_WEAK_PASSWORDS = {
    "password", "123456", "12345678", "123456789", "qwerty", "password123",
    "111111", "123123", "admin", "welcome", "login", "iloveyou", "secret",
    "pass123", "abc123", "monkey", "dragon", "football", "baseball", "master",
    "superman", "trustno1", "letmein", "sunshine", "princess", "starwars"
}

KEYBOARD_SEQUENCES = [
    "qwerty", "asdfgh", "zxcvbn", "qwertz", "azerty", "123456", "234567",
    "345678", "456789", "567890", "678901", "098765", "987654", "876543",
    "765432", "654321", "543210"
]


@dataclass
class AuditReport:
    length: int
    has_lowercase: bool
    has_uppercase: bool
    has_digits: bool
    has_symbols: bool
    character_set_size: int
    estimated_entropy_bits: float
    is_common_weak: bool
    detected_sequences: list[str]
    has_repeated_characters: bool
    strength_score: int  # 0 to 100
    rating: str          # Very Weak, Weak, Fair, Strong, Very Strong
    recommendations: list[str]


class PasswordSecurityAuditor:
    """
    Performs completely local, in-memory cryptographic and heuristic evaluation of passwords.
    Never persists, logs, or transmits passwords.
    """

    @classmethod
    def audit(cls, password: str) -> AuditReport:
        if not password:
            return AuditReport(
                length=0,
                has_lowercase=False,
                has_uppercase=False,
                has_digits=False,
                has_symbols=False,
                character_set_size=0,
                estimated_entropy_bits=0.0,
                is_common_weak=True,
                detected_sequences=[],
                has_repeated_characters=False,
                strength_score=0,
                rating="Very Weak",
                recommendations=["Password cannot be empty. Please enter a valid password."]
            )

        length = len(password)
        has_lower = bool(re.search(r"[a-z]", password))
        has_upper = bool(re.search(r"[A-Z]", password))
        has_digits = bool(re.search(r"[0-9]", password))
        has_symbols = bool(re.search(r"[^a-zA-Z0-9]", password))

        # Calculate character set pool size R
        pool_size = 0
        if has_lower:
            pool_size += 26
        if has_upper:
            pool_size += 26
        if has_digits:
            pool_size += 10
        if has_symbols:
            pool_size += 33

        # Shannon entropy calculation: E = length * log2(pool_size)
        entropy = round(length * math.log2(pool_size), 1) if pool_size > 0 else 0.0

        # Check common dictionary passwords
        pwd_lower = password.lower().strip()
        is_common = pwd_lower in COMMON_WEAK_PASSWORDS or any(c in pwd_lower for c in ["password", "admin", "welcome", "qwerty"])

        # Detect sequences
        detected_seqs = []
        for seq in KEYBOARD_SEQUENCES:
            if seq in pwd_lower:
                detected_seqs.append(f"Keyboard/number sequence: '{seq}'")

        # Detect 3+ consecutive alphabetic sequences (e.g. abc, def, cba)
        for i in range(len(pwd_lower) - 2):
            sub = pwd_lower[i:i+3]
            if len(sub) == 3 and sub.isalpha():
                if ord(sub[1]) - ord(sub[0]) == 1 and ord(sub[2]) - ord(sub[1]) == 1:
                    detected_seqs.append(f"Ascending alphabetic sequence: '{sub}'")
                elif ord(sub[0]) - ord(sub[1]) == 1 and ord(sub[1]) - ord(sub[2]) == 1:
                    detected_seqs.append(f"Descending alphabetic sequence: '{sub}'")

        # Detect repeated characters (e.g. 'aaa', '1111')
        has_repeats = bool(re.search(r"(.)\1{2,}", password))

        # Scoring heuristics
        score = 0
        recommendations = []

        # Length scoring (up to 40 pts)
        if length >= 16:
            score += 40
        elif length >= 12:
            score += 30
        elif length >= 8:
            score += 15
        else:
            score += 5
            recommendations.append("Increase password length to at least 12-16 characters.")

        # Variety scoring (up to 30 pts)
        variety_count = sum([has_lower, has_upper, has_digits, has_symbols])
        score += variety_count * 7.5

        if not has_upper:
            recommendations.append("Include uppercase letters (A-Z).")
        if not has_lower:
            recommendations.append("Include lowercase letters (a-z).")
        if not has_digits:
            recommendations.append("Include numeric digits (0-9).")
        if not has_symbols:
            recommendations.append("Include special symbols (!@#$%^&*...).")

        # Entropy bonus (up to 30 pts)
        if entropy >= 70:
            score += 30
        elif entropy >= 50:
            score += 20
        elif entropy >= 35:
            score += 10

        # Penalties
        if is_common:
            score -= 40
            recommendations.append("Avoid common dictionary words and widely known passwords.")
        if detected_seqs:
            score -= 20
            recommendations.append("Eliminate sequential keyboard or numeric runs (e.g. '123456', 'qwerty', 'abc').")
        if has_repeats:
            score -= 15
            recommendations.append("Avoid repetitive characters (e.g. 'aaa', '1111').")

        final_score = int(min(100, max(0, score)))

        if final_score >= 80:
            rating = "Very Strong"
        elif final_score >= 65:
            rating = "Strong"
        elif final_score >= 45:
            rating = "Fair"
        elif final_score >= 25:
            rating = "Weak"
        else:
            rating = "Very Weak"

        if not recommendations:
            recommendations.append("Excellent password hygiene. Maintain regular security reviews.")

        return AuditReport(
            length=length,
            has_lowercase=has_lower,
            has_uppercase=has_upper,
            has_digits=has_digits,
            has_symbols=has_symbols,
            character_set_size=pool_size,
            estimated_entropy_bits=entropy,
            is_common_weak=is_common,
            detected_sequences=list(set(detected_seqs)),
            has_repeated_characters=has_repeats,
            strength_score=final_score,
            rating=rating,
            recommendations=recommendations,
        )
