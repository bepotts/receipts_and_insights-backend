"""
Security utilities
"""

import warnings
from datetime import timedelta
from typing import Optional

from passlib.context import CryptContext

# Suppress deprecation warning from passlib's argon2 handler
# Library is no longer maintained. May need to update to a different library.
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module="passlib.handlers.argon2",
)

# Create a single CryptContext instance for reuse
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Note: Install python-jose to use:
    pip install python-jose[cryptography]
    """
    # TODO: Implement JWT token creation
    # from jose import jwt
    # to_encode = data.copy()
    # if expires_delta:
    #     expire = datetime.utcnow() + expires_delta
    # else:
    #     expire = datetime.utcnow() + timedelta(minutes=15)
    # to_encode.update({"exp": expire})
    # encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    # return encoded_jwt
    return ""
