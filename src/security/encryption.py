"""
Encryption Service.

Handles password hashing, data encryption, and secure token generation.
"""

import base64
import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Enterprise-grade encryption service.

    Provides secure encryption, hashing, and token generation.
    """

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize encryption service.

        Args:
            secret_key: Base secret key for encryption. If not provided,
                       uses environment variable or generates one.
        """
        self._secret_key = secret_key or os.getenv(
            "SECRET_KEY",
            secrets.token_urlsafe(32)
        )
        self._fernet = self._create_fernet()

    def _create_fernet(self) -> Fernet:
        """Create Fernet instance from secret key."""
        # Derive a proper key from the secret
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"flyready_salt_v1",  # Static salt for deterministic key
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(self._secret_key.encode())
        )
        return Fernet(key)

    # =========================================================================
    # Password Hashing
    # =========================================================================

    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password to verify
            hashed: Hashed password to compare against

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except Exception as e:
            logger.warning(f"Password verification error: {e}")
            return False

    # =========================================================================
    # Data Encryption
    # =========================================================================

    def encrypt(self, data: str) -> str:
        """
        Encrypt string data.

        Args:
            data: Plain text data to encrypt

        Returns:
            Encrypted data as base64 string
        """
        encrypted = self._fernet.encrypt(data.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data.

        Args:
            encrypted_data: Encrypted data as base64 string

        Returns:
            Decrypted plain text

        Raises:
            ValueError: If decryption fails
        """
        try:
            decrypted = self._fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data") from e

    def encrypt_dict(self, data: dict) -> str:
        """Encrypt a dictionary as JSON."""
        import json
        return self.encrypt(json.dumps(data))

    def decrypt_dict(self, encrypted_data: str) -> dict:
        """Decrypt to dictionary."""
        import json
        return json.loads(self.decrypt(encrypted_data))

    # =========================================================================
    # Token Generation
    # =========================================================================

    def generate_token(self, length: int = 32) -> str:
        """
        Generate a secure random token.

        Args:
            length: Token length in bytes (output is URL-safe base64)

        Returns:
            Secure random token string
        """
        return secrets.token_urlsafe(length)

    def generate_numeric_code(self, length: int = 6) -> str:
        """
        Generate a numeric verification code.

        Args:
            length: Number of digits

        Returns:
            Numeric code string
        """
        return "".join(str(secrets.randbelow(10)) for _ in range(length))

    def generate_timed_token(
        self,
        data: str,
        expires_minutes: int = 60
    ) -> str:
        """
        Generate a timed token with expiration.

        Args:
            data: Data to include in token
            expires_minutes: Token validity in minutes

        Returns:
            Timed token string
        """
        expires = datetime.utcnow() + timedelta(minutes=expires_minutes)
        payload = f"{data}|{expires.timestamp()}"
        return self.encrypt(payload)

    def verify_timed_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Verify a timed token.

        Args:
            token: Token to verify

        Returns:
            Tuple of (is_valid, data or None)
        """
        try:
            payload = self.decrypt(token)
            data, expires_str = payload.rsplit("|", 1)
            expires = datetime.fromtimestamp(float(expires_str))

            if datetime.utcnow() > expires:
                return False, None

            return True, data
        except Exception:
            return False, None

    # =========================================================================
    # HMAC Signatures
    # =========================================================================

    def sign_data(self, data: str) -> str:
        """
        Create HMAC signature for data.

        Args:
            data: Data to sign

        Returns:
            HMAC signature as hex string
        """
        signature = hmac.new(
            self._secret_key.encode(),
            data.encode(),
            hashlib.sha256
        )
        return signature.hexdigest()

    def verify_signature(self, data: str, signature: str) -> bool:
        """
        Verify HMAC signature.

        Args:
            data: Original data
            signature: Signature to verify

        Returns:
            True if signature is valid
        """
        expected = self.sign_data(data)
        return hmac.compare_digest(expected, signature)

    # =========================================================================
    # Hashing
    # =========================================================================

    def hash_data(self, data: str, algorithm: str = "sha256") -> str:
        """
        Hash data using specified algorithm.

        Args:
            data: Data to hash
            algorithm: Hash algorithm (sha256, sha512, md5)

        Returns:
            Hash as hex string
        """
        hasher = hashlib.new(algorithm)
        hasher.update(data.encode())
        return hasher.hexdigest()


# Singleton instance
encryption_service = EncryptionService()


# Convenience functions
def hash_password(password: str) -> str:
    """Hash a password."""
    return encryption_service.hash_password(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password."""
    return encryption_service.verify_password(password, hashed)
