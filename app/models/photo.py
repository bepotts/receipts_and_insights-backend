"""
Photo database model
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base

if TYPE_CHECKING:
    from app.models.user import User


class Photo(Base):
    """Photo database model for storing photo uploads"""

    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, onupdate=datetime.utcnow
    )

    # Relationship to User
    user: Mapped["User"] = relationship("User", back_populates="photos")
