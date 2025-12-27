"""
Security utilities
"""

from datetime import timedelta
from typing import Optional


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Note: Install passlib and bcrypt to use:
    pip install passlib[bcrypt]
    """
    # TODO: Implement password verification
    # from passlib.context import CryptContext
    # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # return pwd_context.verify(plain_password, hashed_password)
    return False


def get_password_hash(password: str) -> str:
    """
    Hash a password.

    Note: Install passlib and bcrypt to use:
    pip install passlib[bcrypt]
    """
    # TODO: Implement password hashing
    # from passlib.context import CryptContext
    # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # return pwd_context.hash(password)
    return ""


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
