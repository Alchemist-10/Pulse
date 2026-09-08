"""Password hashing (Argon2id, library defaults) and opaque-token helpers.

`pwdlib` not passlib (ADR / backend.md): passlib's last release was 2020.
Session tokens are random and opaque; only their SHA-256 is ever stored
(ADR-0003), so a Redis dump yields nothing usable.
"""

import hashlib
import secrets

from pwdlib import PasswordHash

_hasher = PasswordHash.recommended()

TOKEN_BYTES = 32


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


def new_token() -> str:
    """A fresh opaque token — session token or verification token."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
