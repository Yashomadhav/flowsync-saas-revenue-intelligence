"""Structured logging configuration with request correlation."""
from __future__ import annotations

import os
import sys
from uuid import uuid4

import structlog
from fastapi import Request


def configure_logging() -> None:
    """Configure structlog with JSON output for production, console for dev."""
    env = os.getenv("API_ENV", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    if env == "production":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.stdlib._NAME_TO_LEVEL.get(log_level.lower(), 20)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_request_id(request: Request) -> str:
    """Extract or generate a request correlation ID."""
    return request.headers.get("X-Request-ID", str(uuid4())[:8])
