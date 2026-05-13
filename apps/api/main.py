"""
FlowSync Revenue Intelligence — FastAPI Application Entry Point
"""
from __future__ import annotations

import os
import time
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from auth.rate_limiter import RateLimiter
from db.database import check_db_health
from observability.sentry_setup import init_sentry
from observability.logging_config import configure_logging, get_request_id
from observability.metrics import metrics_collector
from observability.error_handlers import register_error_handlers
from routers import executive, revenue, cohorts, health, funnel, ingest, webhook
from routers.auth_router import router as auth_router
from routers.pipeline import router as pipeline_router

# ---------------------------------------------------------------------------
# Logging & Observability
# ---------------------------------------------------------------------------
configure_logging()
logger = structlog.get_logger()
init_sentry()

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
API_ENV    = os.getenv("API_ENV", "production")

app = FastAPI(
    title="FlowSync Revenue Intelligence API",
    description="""
## FlowSync SaaS Revenue Intelligence Platform

Production-grade BI API serving metrics for:
- **Executive Overview**: MRR, ARR, NRR, churn, active accounts
- **Revenue Movements**: MRR bridge, waterfall, by plan/region
- **Cohort Retention**: Customer and revenue retention heatmaps
- **Customer Health**: Health scores, churn risk, risk flags
- **Funnel & Growth**: Lead→Trial→Paid conversion analytics

All endpoints require authentication via JWT Bearer token or API key.
    """,
    version="2.0.0",
    docs_url=f"{API_PREFIX}/docs" if API_ENV != "production" else "/docs",
    redoc_url=f"{API_PREFIX}/redoc" if API_ENV != "production" else "/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware (order matters — outermost first)
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RateLimiter)


@app.middleware("http")
async def security_headers(request: Request, call_next: Any) -> Any:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next: Any) -> Any:
    """Log all requests with timing and collect metrics."""
    request_id = get_request_id(request)
    start = time.perf_counter()
    response = await call_next(request)
    duration = round((time.perf_counter() - start) * 1000, 2)

    logger.info(
        "request",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration,
    )

    metrics_collector.record_request(request.url.path, duration, response.status_code)

    response.headers["X-Response-Time"] = f"{duration}ms"
    response.headers["X-Request-ID"] = request_id
    return response


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router,      prefix=f"{API_PREFIX}",           tags=["Authentication"])
app.include_router(executive.router, prefix=f"{API_PREFIX}/executive", tags=["Executive Overview"])
app.include_router(revenue.router,   prefix=f"{API_PREFIX}/revenue",   tags=["Revenue Movements"])
app.include_router(cohorts.router,   prefix=f"{API_PREFIX}/cohorts",   tags=["Cohort Retention"])
app.include_router(health.router,    prefix=f"{API_PREFIX}/health",    tags=["Customer Health"])
app.include_router(funnel.router,    prefix=f"{API_PREFIX}/funnel",    tags=["Funnel & Growth"])
app.include_router(ingest.router,    prefix=f"{API_PREFIX}",           tags=["Ingest"])
app.include_router(webhook.router,   prefix=f"{API_PREFIX}",           tags=["Webhooks"])
app.include_router(pipeline_router,  prefix=f"{API_PREFIX}",           tags=["Pipeline"])


# ---------------------------------------------------------------------------
# Core endpoints
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"], summary="Health check")
async def health_check() -> dict:
    """System health check — used by Docker and load balancers."""
    db_status = check_db_health()
    overall = "healthy" if db_status["status"] == "healthy" else "degraded"
    return {
        "status": overall,
        "api": "healthy",
        "database": db_status,
        "version": "2.0.0",
        "environment": API_ENV,
        "pool": {
            "size": db_status.get("pool_size"),
            "checked_out": db_status.get("checked_out"),
        },
    }


@app.get(f"{API_PREFIX}/health", tags=["System"], summary="Versioned health check")
async def versioned_health_check() -> dict:
    """Versioned health check for API clients expecting /api/v1/health."""
    return await health_check()


@app.get("/metrics", tags=["System"], summary="Application metrics")
async def get_metrics() -> dict:
    """Returns request metrics: latency percentiles, error rates, top endpoints."""
    return metrics_collector.get_stats()


@app.get("/", tags=["System"], summary="API root")
async def root() -> dict:
    """API root — returns basic info."""
    return {
        "name": "FlowSync Revenue Intelligence API",
        "version": "2.0.0",
        "docs": f"{API_PREFIX}/docs",
        "health": "/health",
        "auth": f"{API_PREFIX}/auth/login",
    }


# ---------------------------------------------------------------------------
# Exception handlers (structured, safe, Sentry-integrated)
# ---------------------------------------------------------------------------
register_error_handlers(app)


# ---------------------------------------------------------------------------
# Startup / Shutdown (lifespan)
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event() -> None:
    logger.info("startup", environment=API_ENV, prefix=API_PREFIX, version="2.0.0")
    db_status = check_db_health()
    if db_status["status"] != "healthy":
        logger.warning("database_unhealthy_on_startup", details=db_status)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("shutdown")


# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=API_ENV == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
