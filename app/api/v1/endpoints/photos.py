"""
Photo API endpoints
"""

import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.photo import Photo
from app.schemas.photo import Photo as PhotoSchema
from app.utils.photo import get_photo_by_id
from app.utils.user import get_user_by_id

router = APIRouter()

# Configure upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/", response_model=PhotoSchema, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload a photo"""
    # Verify user exists
    get_user_by_id(user_id, db)

    # Validate file type (images only)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Generate unique filename
    file_extension = Path(file.filename).suffix if file.filename else ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    # Save file to disk
    try:
        contents = await file.read()
        file_size = len(contents)

        with open(file_path, "wb") as f:
            f.write(contents)

        # Create photo record in database
        db_photo = Photo(
            user_id=user_id,
            filename=file.filename or unique_filename,
            file_path=str(file_path),
            file_size=file_size,
            mime_type=file.content_type or "image/jpeg",
            title=title,
            description=description,
        )
        db.add(db_photo)
        db.commit()
        db.refresh(db_photo)

        return db_photo
    except Exception as e:
        # Clean up file if database operation fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading photo: {str(e)}",
        )


@router.get("/", response_model=List[PhotoSchema])
def get_photos(
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get all photos, optionally filtered by user_id"""
    query = db.query(Photo)
    if user_id:
        query = query.filter(Photo.user_id == user_id)
    photos = query.offset(skip).limit(limit).all()
    return photos


@router.get("/{photo_id}", response_model=PhotoSchema)
def get_photo(photo_id: int, db: Session = Depends(get_db)):
    """Get a photo by ID"""
    return get_photo_by_id(photo_id, db)


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    """Delete a photo"""
    photo = get_photo_by_id(photo_id, db)

    # Delete file from disk
    file_path = Path(photo.file_path)
    if file_path.exists():
        file_path.unlink()

    # Delete from database
    db.delete(photo)
    db.commit()
    return None
