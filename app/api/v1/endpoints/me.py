"""
Current user (me) API endpoints
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user_session import UserSession
from app.schemas.user import MeResponse

router = APIRouter()


def _unauthorized_with_cleared_cookie(detail: str) -> JSONResponse:
    resp = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": detail},
    )
    resp.set_cookie(
        key="session_token",
        value="",
        max_age=0,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return resp


@router.post("", response_model=MeResponse, status_code=status.HTTP_200_OK)
def me(
    session_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Return the current user's first name, last name, and email from session cookie."""
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

    user = db_session.user
    return MeResponse(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
    )
