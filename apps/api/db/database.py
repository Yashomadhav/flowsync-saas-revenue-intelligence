"""
FlowSync Revenue Intelligence - Database Engine & Session Management
Provides SQLAlchemy engine with retry logic, connection pooling, and health checks.
"""

import logging
import time
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, DisconnectionError

from .config import get_db_config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Declarative base for all ORM models
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Engine factory with retry logic
# ---------------------------------------------------------------------------

def _create_engine_with_retry(config=None):
    """
    Creates a SQLAlchemy engine with exponential backoff retry logic.
    Retries on connection failure up to config.connect_retries times.
    """
    if config is None:
        config = get_db_config()

    url = config.sync_database_url
    engine_kwargs = config.get_engine_kwargs()

    last_error = None
    delay = config.connect_retry_delay

    for attempt in range(1, config.connect_retries + 1):
        try:
            logger.info(
                "Connecting to database (attempt %d/%d)...",
                attempt,
                config.connect_retries,
            )
            engine = create_engine(
                url,
                poolclass=QueuePool,
                **engine_kwargs,
            )
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully.")
            return engine

        except (OperationalError, DisconnectionError, Exception) as exc:
            last_error = exc
            if attempt < config.connect_retries:
                logger.warning(
                    "Database connection attempt %d failed: %s. Retrying in %.1fs...",
                    attempt,
                    str(exc)[:120],
                    delay,
                )
                time.sleep(delay)
                delay = min(delay * config.connect_retry_backoff, config.connect_retry_max_delay)
            else:
                logger.error(
                    "All %d database connection attempts failed. Last error: %s",
                    config.connect_retries,
                    str(exc),
                )

    raise ConnectionError(
        "Could not connect to the database after "
        + str(config.connect_retries)
        + " attempts. Last error: "
        + str(last_error)
    )


# ---------------------------------------------------------------------------
# Schema search path event listener
# ---------------------------------------------------------------------------

def _set_search_path(dbapi_conn, connection_record):
    """Sets the PostgreSQL schema search path on each new connection."""
    config = get_db_config()
    search_path = config.db_schema_search_path
    cursor = dbapi_conn.cursor()
    cursor.execute("SET search_path TO " + search_path)
    cursor.close()


# ---------------------------------------------------------------------------
# Engine & SessionLocal singletons
# ---------------------------------------------------------------------------

_engine = None
_SessionLocal = None


def get_engine():
    """Returns the singleton SQLAlchemy engine, creating it if needed."""
    global _engine
    if _engine is None:
        config = get_db_config()
        _engine = _create_engine_with_retry(config)
        # Register search path listener
        event.listen(_engine, "connect", _set_search_path)
        logger.info("Engine created: %s", config.get_connection_info())
    return _engine


def get_session_factory():
    """Returns the singleton SessionLocal factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


# ---------------------------------------------------------------------------
# FastAPI dependency: get_db()
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.
    Automatically closes the session after the request.

    Usage:
        @router.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Context manager for scripts (non-FastAPI usage)
# ---------------------------------------------------------------------------

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions in scripts and services.

    Usage:
        with get_db_session() as db:
            results = db.execute(text("SELECT ...")).fetchall()
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def check_db_health() -> dict:
    """
    Performs a lightweight database health check.
    Returns a dict with status, latency_ms, and connection info.
    """
    start = time.monotonic()
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT version(), current_database(), current_schema()")
            ).fetchone()
        latency_ms = round((time.monotonic() - start) * 1000, 2)
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "pg_version": result[0].split(" ")[0] + " " + result[0].split(" ")[1] if result else "unknown",
            "database": result[1] if result else "unknown",
            "schema": result[2] if result else "unknown",
            "pool_size": engine.pool.size(),
            "checked_out": engine.pool.checkedout(),
        }
    except Exception as exc:
        latency_ms = round((time.monotonic() - start) * 1000, 2)
        return {
            "status": "unhealthy",
            "latency_ms": latency_ms,
            "error": str(exc)[:200],
        }


# ---------------------------------------------------------------------------
# Schema initialization helper
# ---------------------------------------------------------------------------

def init_schemas(engine=None):
    """
    Creates the raw, staging, marts, and auth schemas if they don't exist.
    Safe to call multiple times (idempotent).
    """
    if engine is None:
        engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS marts"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))
    logger.info("Schemas raw/staging/marts/auth ensured.")


def create_all_tables(engine=None):
    """
    Creates all ORM-mapped tables. Useful for testing and local dev.
    Does NOT replace dbt transformations for production.
    """
    if engine is None:
        engine = get_engine()
    init_schemas(engine)
    Base.metadata.create_all(bind=engine)
    logger.info("All ORM tables created.")
