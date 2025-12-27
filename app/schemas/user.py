"""
User schemas
"""

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """Base user schema with common fields"""

    name: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user"""

    pass


class UserUpdate(BaseModel):
    """Schema for updating a user (all fields optional)"""

    name: str | None = None
    email: EmailStr | None = None


class User(UserBase):
    """Schema for user response"""

    id: int | None = None

    model_config = ConfigDict(from_attributes=True)
