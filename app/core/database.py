"""
Database session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings
from app.models import Base

# Create database engine
engine = create_engine(
    settings.DATABASE_URL or "sqlite:///./receipts.db",
    connect_args={"check_same_thread": False} if "sqlite" in (settings.DATABASE_URL or "") else {},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Database session dependency for FastAPI
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

