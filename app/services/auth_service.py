
import hashlib
import hmac
import secrets


def hash_password(password: str) -> str:
    """Convert a password into a salted PBKDF2 hash."""
    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        600_000,
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Check whether a password matches its stored hash."""
    try:
        salt, expected_hash = stored_hash.split("$", 1)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            600_000,
        ).hex()

        return hmac.compare_digest(actual_hash, expected_hash)

    except (ValueError, AttributeError):
        return False
