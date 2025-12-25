"""
Main application entry point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.database import init_db, close_db
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    print("Starting application...")
    print("--------------------------------")
    print("Initializing database on startup")
    init_db()
    yield
    # Shutdown
    print("Shutting down application...")
    print("--------------------------------")
    print("Closing database on shutdown")
    close_db()


app = FastAPI(
    title="Receipts and Insights Backend",
    description="Backend API for Receipts and Insights application",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api/v1")


def main():
    """Application entry point"""
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()

