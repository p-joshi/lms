"""Helpers for the login view."""

import binascii
import hashlib


__all__ = ["check_password"]


def check_password(password: str, expected_pw_hash: str, salt: str):
    pw_hash = binascii.hexlify(
        hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf8"), salt.encode("utf8"), 1000000
        )
    )
    return expected_pw_hash.encode("utf8") == pw_hash