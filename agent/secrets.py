"""Small secret-sealing helper for user-owned API keys.

The application stores per-user service keys as authenticated ciphertext. The
master secret must come from an instance-level secret, for example
`APP_SECRET_KEY`.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os


SECRET_BOX_VERSION = "da1"
_SALT_BYTES = 16
_NONCE_BYTES = 16
_TAG_BYTES = 32


class SecretBoxError(ValueError):
    """Raised when a secret cannot be sealed or opened safely."""


def mask_secret(secret: str) -> str:
    """Return a safe display hint for an API key."""
    value = secret.strip()
    if not value:
        return ""
    if len(value) <= 8:
        return f"{value[:2]}...{value[-2:]}"
    prefix = value[: min(6, len(value) - 4)]
    return f"{prefix}...{value[-4:]}"


def seal_secret(secret: str, app_secret: str) -> str:
    """Encrypt and authenticate a user-owned secret for database storage."""
    if not secret:
        raise SecretBoxError("secret is required")
    if not app_secret or len(app_secret) < 16:
        raise SecretBoxError("app secret must be at least 16 characters")

    salt = os.urandom(_SALT_BYTES)
    nonce = os.urandom(_NONCE_BYTES)
    keys = _derive_keys(app_secret=app_secret, salt=salt)
    plaintext = secret.encode("utf-8")
    ciphertext = _xor_bytes(plaintext, _keystream(keys.encryption_key, nonce, len(plaintext)))
    signed = salt + nonce + ciphertext
    tag = hmac.new(keys.signing_key, signed, hashlib.sha256).digest()
    payload = base64.urlsafe_b64encode(signed + tag).decode("ascii")
    return f"{SECRET_BOX_VERSION}.{payload}"


def open_secret(sealed_secret: str, app_secret: str) -> str:
    """Decrypt a sealed secret after validating its authentication tag."""
    if not sealed_secret.startswith(f"{SECRET_BOX_VERSION}."):
        raise SecretBoxError("unsupported sealed secret version")
    if not app_secret or len(app_secret) < 16:
        raise SecretBoxError("app secret must be at least 16 characters")

    try:
        raw = base64.urlsafe_b64decode(sealed_secret.split(".", 1)[1].encode("ascii"))
    except (ValueError, IndexError) as exc:
        raise SecretBoxError("malformed sealed secret") from exc

    minimum_length = _SALT_BYTES + _NONCE_BYTES + _TAG_BYTES + 1
    if len(raw) < minimum_length:
        raise SecretBoxError("sealed secret is too short")

    body = raw[:-_TAG_BYTES]
    tag = raw[-_TAG_BYTES:]
    salt = body[:_SALT_BYTES]
    nonce = body[_SALT_BYTES : _SALT_BYTES + _NONCE_BYTES]
    ciphertext = body[_SALT_BYTES + _NONCE_BYTES :]
    keys = _derive_keys(app_secret=app_secret, salt=salt)
    expected_tag = hmac.new(keys.signing_key, body, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected_tag):
        raise SecretBoxError("sealed secret authentication failed")

    plaintext = _xor_bytes(ciphertext, _keystream(keys.encryption_key, nonce, len(ciphertext)))
    try:
        return plaintext.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SecretBoxError("sealed secret is not valid utf-8") from exc


class _DerivedKeys:
    def __init__(self, encryption_key: bytes, signing_key: bytes) -> None:
        self.encryption_key = encryption_key
        self.signing_key = signing_key


def _derive_keys(app_secret: str, salt: bytes) -> _DerivedKeys:
    material = hashlib.pbkdf2_hmac(
        "sha256",
        app_secret.encode("utf-8"),
        salt,
        200_000,
        dklen=64,
    )
    return _DerivedKeys(encryption_key=material[:32], signing_key=material[32:])


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < length:
        counter_bytes = counter.to_bytes(8, "big")
        output.extend(hmac.new(key, nonce + counter_bytes, hashlib.sha256).digest())
        counter += 1
    return bytes(output[:length])


def _xor_bytes(left: bytes, right: bytes) -> bytes:
    return bytes(left_byte ^ right_byte for left_byte, right_byte in zip(left, right))
