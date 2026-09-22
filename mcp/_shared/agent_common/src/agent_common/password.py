"""Shared PBKDF2 password hashing utilities.

Used by OTDS-MCP (to store and check credentials) and DA-MCP (to verify the
DA -> OTDS authentication path during login_test) so both agents check
credentials the same real way instead of one trusting a canned result from
the other.
"""
from __future__ import annotations

import hashlib
import os

_ITERATIONS = 200_000


def hash_password(password: str, salt: bytes | None = None) -> dict[str, str]:
    salt = salt if salt is not None else os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS).hex()
    return {"salt": salt.hex(), "password_hash": digest}


def verify_password(password: str, salt_hex: str, password_hash: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS).hex()
    return candidate == password_hash
