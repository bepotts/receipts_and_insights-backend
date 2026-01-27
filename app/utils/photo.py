"""
Photo utility functions
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.photo import Photo


def get_photo_by_id(photo_id: int, db: Session) -> Photo:
    """
    Get a photo by photo ID. Raises HTTPException if photo not found.

    Args:
        photo_id: The ID of the photo to retrieve
        db: Database session

    Returns:
        Photo object if found

    Raises:
        HTTPException: 404 if photo not found
    """
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with id {photo_id} not found",
        )
    return photo
