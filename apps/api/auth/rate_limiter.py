"""Token bucket rate limiter middleware."""
from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Any

import structlog
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", "10"))

EXEMPT_PATHS = {"/health", "/", "/docs", "/redoc", "/openapi.json"}


class RateLimiter(BaseHTTPMiddleware):
    def __init__(self, app: Any, requests_per_minute: int = RATE_LIMIT_PER_MINUTE):
        super().__init__(app)
        self.rate = requests_per_minute / 60.0
        self.max_tokens = requests_per_minute
        self._buckets: dict[str, tuple[float, float]] = defaultdict(
            lambda: (float(self.max_tokens), time.monotonic())
        )

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        client_key = self._get_client_key(request)
        tokens, last_time = self._buckets[client_key]

        now = time.monotonic()
        elapsed = now - last_time
        tokens = min(self.max_tokens, tokens + elapsed * self.rate)

        if tokens < 1:
            retry_after = int((1 - tokens) / self.rate) + 1
            logger.warning("rate_limited", client=client_key, path=request.url.path)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limited",
                    "message": f"Rate limit exceeded. Try again in {retry_after}s.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        tokens -= 1
        self._buckets[client_key] = (tokens, now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_tokens)
        response.headers["X-RateLimit-Remaining"] = str(int(tokens))
        return response

    def _get_client_key(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
