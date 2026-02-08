"""
Photo schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PhotoBase(BaseModel):
    """Base photo schema with common fields"""

    filename: str
    file_path: str
    file_size: int
    mime_type: str
    title: Optional[str] = None
    description: Optional[str] = None


class PhotoCreate(PhotoBase):
    """Schema for creating a photo"""

    user_id: int


class Photo(PhotoBase):
    """Schema for photo response"""

    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PhotoWithFile(Photo):
    """Schema for photo response including file content from disk (base64)."""

    file_content: Optional[str] = None  # base64-encoded file bytes, None if file missing
