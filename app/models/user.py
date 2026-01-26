"""
User database model
"""

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.photo import Photo
    from app.models.user_session import UserSession


class Base(DeclarativeBase):
    """Base class for all database models"""

    pass


class User(Base):
    """User database model"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String, nullable=False)

    # Relationship to UserSession
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    # Relationship to Photo
    photos: Mapped[list["Photo"]] = relationship(
        "Photo", back_populates="user", cascade="all, delete-orphan"
    )
