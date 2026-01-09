"""
Authentication API endpoints
"""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.user_session import UserSession
from app.schemas.user import User as UserSchema
from app.schemas.user import UserCreate
from app.utils.email import format_email

router = APIRouter()


@router.post("/login", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def login(user: UserCreate, response: Response, db: Session = Depends(get_db)):
    """Create a new user"""
    formatted_email = format_email(str(user.email))
    # Check if user with email already exists
    db_user = db.query(User).filter(User.email == formatted_email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    hashed_password = get_password_hash(user.password)
    db_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=formatted_email,
        password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create a new user session
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=30
    )  # Session expires in 30 days

    user_session = UserSession(
        user_id=db_user.id,
        session_token=session_token,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(user_session)
    db.commit()

    # Set cookie with session_token
    response.set_cookie(
        key="session_token",
        value=session_token,
        expires=expires_at,
        httponly=True,
        secure=True,
        samesite="lax",
    )

    # Return user with session_token
    user_dict = {
        "id": db_user.id,
        "first_name": db_user.first_name,
        "last_name": db_user.last_name,
        "email": db_user.email,
        "session_token": session_token,
    }
    return user_dict
