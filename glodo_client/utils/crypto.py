"""
Cryptographic utilities for Glodo Cloud client.

Uses AES-GCM for symmetric encryption with a shared secret
configured in odoo.conf.
"""

import base64
import json
import logging
import os
import time
from functools import wraps

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from werkzeug.exceptions import BadRequest, Forbidden

from odoo.http import request

_logger = logging.getLogger(__name__)


class GlodoCryptoError(Exception):
    """Base exception for Glodo cryptographic operations."""

    pass


class GlodoAuthenticationError(GlodoCryptoError):
    """Exception raised when authentication fails."""

    pass


class GlodoTokenExpiredError(GlodoCryptoError):
    """Exception raised when a token has expired."""

    pass


class AESGCMCrypto:
    """
    AES-GCM encryption/decryption for Glodo Cloud communication.

    All requests between server and client use this symmetric encryption
    with a shared secret configured in odoo.conf.
    """

    def __init__(self, shared_secret: bytes, ttl: int = 60):
        """
        Initialize the crypto handler.

        Args:
            shared_secret: 32-byte AES-256 key
            ttl: Time-to-live for tokens in seconds (default: 60)
        """
        if len(shared_secret) != 32:
            raise GlodoCryptoError("Shared secret must be 32 bytes (AES-256)")
        self.shared_secret = shared_secret
        self.ttl = ttl
        self._aesgcm = AESGCM(shared_secret)

    def encrypt(self, payload):
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

    def decrypt(self, encrypted_data):
        """
        Decrypt and verify an AES-GCM encrypted payload.

        Args:
            encrypted_data: Dictionary with 'iv' and 'ciphertext'

        Returns:
            Decrypted payload dictionary

        Raises:
            GlodoAuthenticationError: If decryption/authentication fails
            GlodoTokenExpiredError: If timestamp is too old
        """
        try:
            iv = base64.b64decode(encrypted_data["iv"])
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])
        except (KeyError, ValueError) as e:
            raise GlodoAuthenticationError(f"Invalid encrypted data format: {e}") from e

        try:
            plaintext = self._aesgcm.decrypt(iv, ciphertext, None)
            payload = json.loads(plaintext.decode("utf-8"))
        except Exception as e:
            raise GlodoAuthenticationError(f"Decryption failed: {e}") from e

        # Verify timestamp
        ts = payload.get("ts")
        if ts is None:
            raise GlodoAuthenticationError("Missing timestamp in payload")

        age = int(time.time()) - int(ts)
        if self.ttl is not None and age > self.ttl:
            raise GlodoTokenExpiredError(
                f"Token expired: {age} seconds old (max: {self.ttl})"
            )

        return payload


def get_client_config():
    """
    Get the client's instance ID and shared secret from config.

    Config keys in odoo.conf:
        glodo_cloud_instance_id: Unique instance identifier
        glodo_cloud_shared_secret: Base64-encoded AES-256 key

    Returns:
        Tuple of (instance_id, shared_secret) or (None, None) if not configured
    """
    from odoo.tools import config

    instance_id = config.get("glodo_cloud_instance_id")
    secret_b64 = config.get("glodo_cloud_shared_secret")

    if not instance_id or not secret_b64:
        return None, None

    try:
        shared_secret = base64.b64decode(secret_b64)
    except Exception:
        _logger.error("Invalid glodo_cloud_shared_secret in config")
        return None, None

    return instance_id, shared_secret


def glodo_authenticated(func):
    """
    Decorator for controllers that require Glodo Cloud authentication.

    Verifies the request is encrypted with the correct shared secret
    and the timestamp is valid.

    Supports both JSON body and form-encoded data (for become redirects).
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        instance_id, shared_secret = get_client_config()

        if not instance_id or not shared_secret:
            _logger.warning("Glodo Cloud request rejected: not configured")
            raise Forbidden("This instance is not configured for Glodo Cloud")

        # Try to get encrypted data from JSON body or form parameters
        encrypted_data = None

        # First try JSON body
        try:
            raw_data = request.httprequest.get_data()
            if raw_data:
                encrypted_data = json.loads(raw_data)
        except (TypeError, ValueError):
            # Not valid JSON - will try form parameters below
            _logger.debug("Request body is not valid JSON, trying form parameters")

        # Fall back to form parameters (for become redirect)
        if not encrypted_data or "iv" not in encrypted_data:
            iv = request.params.get("iv")
            ciphertext = request.params.get("ciphertext")
            if iv and ciphertext:
                encrypted_data = {"iv": iv, "ciphertext": ciphertext}

        if not encrypted_data:
            raise BadRequest("Invalid request payload")

        if "iv" not in encrypted_data or "ciphertext" not in encrypted_data:
            raise BadRequest("Missing encryption fields (iv, ciphertext)")

        # Decrypt and verify
        try:
            crypto = AESGCMCrypto(shared_secret, ttl=60)
            payload = crypto.decrypt(encrypted_data)
        except GlodoTokenExpiredError as e:
            _logger.warning("Glodo Cloud request rejected: token expired - %s", e)
            raise BadRequest("Request token has expired") from e
        except GlodoAuthenticationError as e:
            _logger.warning("Glodo Cloud request rejected: auth failed - %s", e)
            raise Forbidden("Authentication failed") from e
        except GlodoCryptoError as e:
            _logger.warning("Glodo Cloud request rejected: crypto error - %s", e)
            raise BadRequest("Cryptographic error") from e

        # Attach decrypted payload to request
        request.glodo_payload = payload
        return func(*args, **kwargs)

    return wrapper
