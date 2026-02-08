"""
Photo API endpoints
"""

import base64
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.v1.endpoints.me import _unauthorized_with_cleared_cookie
from app.core.database import get_db
from app.models.photo import Photo
from app.models.user_session import UserSession
from app.schemas.photo import Photo as PhotoSchema
from app.schemas.photo import PhotoWithFile
from app.utils.photo import get_photo_by_id

router = APIRouter()

# Configure upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=PhotoSchema, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    session_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Upload a photo. User is identified by session_token cookie."""
    if not session_token:
        return _unauthorized_with_cleared_cookie("Missing session token")

    now = datetime.now(timezone.utc)
    db_session = (
        db.query(UserSession)
        .filter(
            UserSession.session_token == session_token,
            UserSession.is_active,
            UserSession.expires_at > now,
        )
        .first()
    )
    if not db_session:
        return _unauthorized_with_cleared_cookie("Invalid or expired session")

    user_id = db_session.user_id

    # Validate file type (images only)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Store in user's unique directory (named by user id)
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_extension = Path(file.filename).suffix if file.filename else ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = user_dir / unique_filename

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


@router.get("/", response_model=List[PhotoWithFile])
def get_photos(
    session_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Get all photos for the current user with file content from each file_path."""
    if not session_token:
        return _unauthorized_with_cleared_cookie("Missing session token")

    now = datetime.now(timezone.utc)
    db_session = (
        db.query(UserSession)
        .filter(
            UserSession.session_token == session_token,
            UserSession.is_active,
            UserSession.expires_at > now,
        )
        .first()
    )
    if not db_session:
        return _unauthorized_with_cleared_cookie("Invalid or expired session")

    user_id = db_session.user_id
    photos = db.query(Photo).filter(Photo.user_id == user_id).all()
    result = []
    for photo in photos:
        file_content = None
        file_path = Path(photo.file_path)
        if file_path.exists():
            try:
                raw = file_path.read_bytes()
                file_content = base64.b64encode(raw).decode("ascii")
            except OSError:
                pass
        result.append(
            PhotoWithFile(
                **PhotoSchema.model_validate(photo).model_dump(),
                file_content=file_content,
            )
        )
    return result


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
