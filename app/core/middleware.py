"""
Middleware configuration for the application
"""

import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Maximum body size to log in full (bytes); larger payloads are truncated
MAX_BODY_LOG_SIZE = 10 * 1024  # 10 KB


def _format_body_for_logging(body: bytes) -> str:
    """Format request/response body for logging, handling binary and large payloads."""
    if not body:
        return "(empty)"
    if len(body) > MAX_BODY_LOG_SIZE:
        body_preview = body[:MAX_BODY_LOG_SIZE]
        truncated = f"... [truncated, {len(body)} total bytes]"
    else:
        body_preview = body
        truncated = ""
    try:
        return body_preview.decode("utf-8") + truncated
    except UnicodeDecodeError:
        return f"<binary payload, {len(body)} bytes>" + truncated


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs every request and response entering and leaving the application.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        # Read and log request body (must be done before call_next consumes it)
        body = await request.body()

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        # Create new request with body so downstream handlers can read it
        request = Request(request.scope, receive)

        body_str = _format_body_for_logging(body)
        logger.info(
            "Request IN: {} {} (client: {}) body: {}",
            method,
            path,
            client_host,
            body_str,
        )

        response = await call_next(request)

        # Capture response body for logging
        response_body = b""
        if hasattr(response, "body_iterator"):
            response_body = b"".join([chunk async for chunk in response.body_iterator])
            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=getattr(response, "media_type", None),
            )

        duration_ms = (time.perf_counter() - start_time) * 1000
        response_body_str = _format_body_for_logging(response_body)
        logger.info(
            "Response OUT: {} {} -> {} ({} ms) body: {}",
            method,
            path,
            response.status_code,
            round(duration_ms, 2),
            response_body_str,
        )

        return response


def add_request_logging_middleware(app: FastAPI) -> None:
    """
    Add request logging middleware to the FastAPI application.
    Logs every request with method, path, client, status code, and duration.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(RequestLoggingMiddleware)


def add_cors_middleware(app: FastAPI) -> None:
    """
    Add CORS middleware to the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
