"""
Main application entry point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.database import close_db, init_db
from app.core.middleware import add_cors_middleware


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

def create_app() -> FastAPI:
    """Create a FastAPI application instance"""
    app = FastAPI(
        title="Receipts and Insights Backend",
        description="Backend API for Receipts and Insights application",
        version="0.1.0",
        lifespan=lifespan,
    )
    add_cors_middleware(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()


def main():
    """Application entry point"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
