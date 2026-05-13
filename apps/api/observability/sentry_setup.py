"""Sentry SDK initialization for error tracking and performance monitoring."""
from __future__ import annotations

import os

import structlog

logger = structlog.get_logger(__name__)

SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", os.getenv("API_ENV", "development"))
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))


def init_sentry() -> bool:
    """
    Initialize Sentry if DSN is configured.
    Returns True if Sentry was initialized, False otherwise.
    """
    if not SENTRY_DSN:
        logger.info("sentry_disabled", reason="SENTRY_DSN not set")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=SENTRY_ENVIRONMENT,
            traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoggingIntegration(level=None, event_level="ERROR"),
            ],
            send_default_pii=False,
            before_send=_filter_events,
        )

        logger.info(
            "sentry_initialized",
            environment=SENTRY_ENVIRONMENT,
            traces_rate=SENTRY_TRACES_SAMPLE_RATE,
        )
        return True

    except ImportError:
        logger.warning("sentry_not_installed", hint="pip install sentry-sdk[fastapi]")
        return False
    except Exception as exc:
        logger.error("sentry_init_failed", error=str(exc))
        return False


def _filter_events(event: dict, hint: dict) -> dict | None:
    """Filter out noisy or sensitive events before sending to Sentry."""
    if "exc_info" in hint:
        exc_type = hint["exc_info"][0]
        if exc_type and exc_type.__name__ in ("KeyboardInterrupt", "SystemExit"):
            return None

    if "request" in event:
        request_data = event["request"]
        headers = request_data.get("headers", {})
        for sensitive in ("authorization", "x-api-key", "cookie"):
            if sensitive in headers:
                headers[sensitive] = "[Filtered]"

    return event
