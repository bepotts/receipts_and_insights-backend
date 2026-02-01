"""
Main application entry point
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.v1.api import api_router
from app.config import settings
from app.core.database import close_db, init_db
from app.core.middleware import add_cors_middleware, add_request_logging_middleware


def _setup_logging() -> None:
    """Configure logging to write to the logs directory."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "app.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    formatter = logging.Formatter(log_format)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Also keep console output
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    _setup_logging()
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


def create_app() -> FastAPI:
    """Create a FastAPI application instance"""
    app = FastAPI(
        title="Receipts and Insights Backend",
        description="Backend API for Receipts and Insights application",
        version="0.1.0",
        lifespan=lifespan,
    )
    add_cors_middleware(app)
    add_request_logging_middleware(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()


def main():
    """Application entry point"""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
