"""
Cryptographic utilities for Glodo Cloud Server.

Uses AES-GCM for secure communication with clients.
"""

import base64
import json
import logging
import os
import time
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_logger = logging.getLogger(__name__)


class GlodoCryptoError(Exception):
    """Base exception for Glodo cryptographic operations."""

    pass


def generate_shared_secret() -> str:
    """
    Generate a new AES-256 shared secret.

    Returns:
        Base64-encoded 32-byte secret
    """
    return base64.b64encode(os.urandom(32)).decode("ascii")


class AESGCMCrypto:
    """
    AES-GCM encryption/decryption for Glodo Cloud communication.

    Used by the server to communicate with enrolled clients.
    """

    def __init__(self, shared_secret: bytes, ttl: int | None = 60):
        """
        Initialize the crypto handler.

        Args:
            shared_secret: 32-byte AES-256 key
            ttl: Time-to-live for tokens in seconds (default: 60, None to disable)
        """
        if len(shared_secret) != 32:
            raise GlodoCryptoError("Shared secret must be 32 bytes (AES-256)")
        self.shared_secret = shared_secret
        self.ttl = ttl
        self._aesgcm = AESGCM(shared_secret)

    def encrypt(self, payload: dict[str, Any]) -> dict[str, str]:
        """
        Encrypt a payload with AES-GCM.

        Adds a timestamp to the payload for replay protection.

        Args:
            payload: Dictionary to encrypt

        Returns:
            Dictionary with 'iv' and 'ciphertext' (base64 encoded)
        """
        payload_with_ts = payload.copy()
        payload_with_ts["ts"] = int(time.time())

        iv = os.urandom(12)  # 96-bit IV for GCM
        plaintext = json.dumps(payload_with_ts).encode("utf-8")
        ciphertext = self._aesgcm.encrypt(iv, plaintext, None)

        return {
            "iv": base64.b64encode(iv).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        }

    def decrypt(self, encrypted_data: dict[str, str]) -> dict[str, Any]:
        """
        Decrypt and verify an AES-GCM encrypted payload.

        Args:
            encrypted_data: Dictionary with 'iv' and 'ciphertext'

        Returns:
            Decrypted payload dictionary
        """
        try:
            iv = base64.b64decode(encrypted_data["iv"])
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])
        except (KeyError, ValueError) as e:
            raise GlodoCryptoError(f"Invalid encrypted data format: {e}") from e

        try:
            plaintext = self._aesgcm.decrypt(iv, ciphertext, None)
            payload = json.loads(plaintext.decode("utf-8"))
        except Exception as e:
            raise GlodoCryptoError(f"Decryption failed: {e}") from e

        # Verify timestamp if TTL is set
        if self.ttl is not None:
            ts = payload.get("ts")
            if ts is None:
                raise GlodoCryptoError("Missing timestamp in payload")
            age = int(time.time()) - int(ts)
            if age > self.ttl:
                raise GlodoCryptoError(
                    f"Token expired: {age} seconds old (max: {self.ttl})"
                )

        return payload
