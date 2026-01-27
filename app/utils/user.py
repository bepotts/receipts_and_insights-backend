"""
User utility functions
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_id(user_id: int, db: Session) -> User:
    """
    Get a user by user ID. Raises HTTPException if user not found.

    Args:
        user_id: The ID of the user to retrieve
        db: Database session

    Returns:
        User object if found

    Raises:
        HTTPException: 404 if user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    return user
