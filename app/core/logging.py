"""
Loguru logging configuration for the application.
"""

import logging
import sys
from pathlib import Path

from loguru import logger

from app.config import settings


def setup_logging() -> None:
    """
    Configure loguru: remove default handler, add console and file sinks,
    and intercept standard library logging.
    """
    # Remove default handler so we control all sinks
    logger.remove()

    log_level = settings.LOG_LEVEL.upper()
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Console sink (stderr)
    logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        colorize=True,
    )

    # File sink: one file per day (e.g. app_2025-02-08.log)
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "app_{time:YYYY-MM-DD}.log"

    logger.add(
        log_file,
        format=log_format,
        level=log_level,
        rotation="00:00",  # rotate at midnight so each day gets a new file
        retention="7 days",
        compression="zip",
        encoding="utf-8",
    )

    # Intercept standard library logging so logging.getLogger() goes to loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers = [InterceptHandler()]
