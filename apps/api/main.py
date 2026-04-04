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

from db.database import check_db_health
from routers import executive, revenue, cohorts, health, funnel, ingest, webhook

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

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

All metrics follow standard SaaS definitions (MRR, ARR, NRR, GRR, ARPA).
    """,
    version="1.0.0",
    docs_url=f"{API_PREFIX}/docs" if API_ENV != "production" else "/docs",
    redoc_url=f"{API_PREFIX}/redoc" if API_ENV != "production" else "/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware
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
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def log_requests(request: Request, call_next: Any) -> Any:
    """Log all requests with timing."""
    start = time.perf_counter()
    response = await call_next(request)
    duration = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration,
    )
    response.headers["X-Response-Time"] = f"{duration}ms"
    return response


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(executive.router, prefix=f"{API_PREFIX}/executive", tags=["Executive Overview"])
app.include_router(revenue.router,   prefix=f"{API_PREFIX}/revenue",   tags=["Revenue Movements"])
app.include_router(cohorts.router,   prefix=f"{API_PREFIX}/cohorts",   tags=["Cohort Retention"])
app.include_router(health.router,    prefix=f"{API_PREFIX}/health",    tags=["Customer Health"])
app.include_router(funnel.router,    prefix=f"{API_PREFIX}/funnel",    tags=["Funnel & Growth"])
app.include_router(ingest.router,    prefix=f"{API_PREFIX}",           tags=["Ingest"])
app.include_router(webhook.router,   prefix=f"{API_PREFIX}",           tags=["Webhooks"])


# ---------------------------------------------------------------------------
# Core endpoints
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"], summary="Health check")
async def health_check() -> dict:
    """System health check — used by Docker and load balancers."""
    db_status = check_db_health()
    return {
        "status": "healthy" if db_status["status"] == "healthy" else "degraded",
        "api": "healthy",
        "database": db_status,
        "version": "1.0.0",
        "environment": API_ENV,
    }


@app.get(f"{API_PREFIX}/health", tags=["System"], summary="Versioned health check")
async def versioned_health_check() -> dict:
    """Versioned health check for API clients expecting /api/v1/health."""
    return await health_check()


@app.get("/", tags=["System"], summary="API root")
async def root() -> dict:
    """API root — returns basic info."""
    return {
        "name": "FlowSync Revenue Intelligence API",
        "version": "1.0.0",
        "docs": f"{API_PREFIX}/docs",
        "health": "/health",
    }


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Any) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url.path)},
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Any) -> JSONResponse:
    logger.error("unhandled_error", path=str(request.url.path), error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# Startup / Shutdown
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event() -> None:
    logger.info("startup", environment=API_ENV, prefix=API_PREFIX)
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
