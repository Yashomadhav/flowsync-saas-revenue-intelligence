"""
FlowSync Revenue Intelligence - Database Configuration
Environment-based database config using Pydantic Settings.
Supports connection pooling, SSL, and read replicas.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    from pydantic import BaseSettings, Field  # type: ignore


class DatabaseConfig(BaseSettings):
    """Database connection configuration loaded from environment variables."""

    # Core connection
    database_url: str = Field(
        default="postgresql://flowsync:flowsync_secret_change_me@localhost:5432/flowsync_bi",
        env="DATABASE_URL",
    )

    # Individual components (used when DATABASE_URL is not set)
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="flowsync_bi", env="POSTGRES_DB")
    postgres_user: str = Field(default="flowsync", env="POSTGRES_USER")
    postgres_password: str = Field(
        default="flowsync_secret_change_me", env="POSTGRES_PASSWORD"
    )

    # Connection pool settings
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=1800, env="DB_POOL_RECYCLE")
    pool_pre_ping: bool = Field(default=True, env="DB_POOL_PRE_PING")

    # Retry logic
    connect_retries: int = Field(default=5, env="DB_CONNECT_RETRIES")
    connect_retry_delay: float = Field(default=2.0, env="DB_CONNECT_RETRY_DELAY")
    connect_retry_backoff: float = Field(default=2.0, env="DB_CONNECT_RETRY_BACKOFF")
    connect_retry_max_delay: float = Field(default=30.0, env="DB_CONNECT_RETRY_MAX_DELAY")

    # SSL settings
    db_ssl_mode: Optional[str] = Field(default=None, env="DB_SSL_MODE")
    db_ssl_cert: Optional[str] = Field(default=None, env="DB_SSL_CERT")
    db_ssl_key: Optional[str] = Field(default=None, env="DB_SSL_KEY")
    db_ssl_root_cert: Optional[str] = Field(default=None, env="DB_SSL_ROOT_CERT")

    # Schema search path
    db_schema_search_path: str = Field(
        default="marts,staging,raw,public",
        env="DB_SCHEMA_SEARCH_PATH",
    )

    # Application settings
    api_env: str = Field(default="development", env="API_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    echo_sql: bool = Field(default=False, env="DB_ECHO_SQL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def effective_database_url(self) -> str:
        """
        Returns the effective DATABASE_URL.
        If DATABASE_URL env var is explicitly set, use it.
        Otherwise construct from individual POSTGRES_* components.
        """
        env_url = os.environ.get("DATABASE_URL", "")
        if env_url:
            return env_url
        user = self.postgres_user
        pwd = self.postgres_password
        host = self.postgres_host
        port = self.postgres_port
        db = self.postgres_db
        return "postgresql://" + user + ":" + pwd + "@" + host + ":" + str(port) + "/" + db

    @property
    def async_database_url(self) -> str:
        """Async version of the database URL using asyncpg driver."""
        url = self.effective_database_url
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)

    @property
    def sync_database_url(self) -> str:
        """Sync version of the database URL using psycopg2 driver."""
        url = self.effective_database_url
        if "+asyncpg" in url:
            return url.replace("+asyncpg", "", 1)
        return url

    @property
    def is_production(self) -> bool:
        return self.api_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.api_env.lower() == "development"

    def get_engine_kwargs(self) -> dict:
        """Returns SQLAlchemy engine keyword arguments."""
        kwargs = dict(
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=self.pool_pre_ping,
            echo=self.echo_sql and self.is_development,
        )

        if self.db_ssl_mode:
            connect_args = {"sslmode": self.db_ssl_mode}
            if self.db_ssl_cert:
                connect_args["sslcert"] = self.db_ssl_cert
            if self.db_ssl_key:
                connect_args["sslkey"] = self.db_ssl_key
            if self.db_ssl_root_cert:
                connect_args["sslrootcert"] = self.db_ssl_root_cert
            kwargs["connect_args"] = connect_args

        return kwargs

    def get_connection_info(self) -> dict:
        """Returns sanitized connection info (password masked) for logging."""
        url = self.effective_database_url
        if "@" in url:
            prefix = url.split("@")[0]
            suffix = url.split("@")[1]
            if ":" in prefix:
                user_part = prefix.rsplit(":", 1)[0]
                masked = user_part + ":***@" + suffix
            else:
                masked = prefix + "@" + suffix
        else:
            masked = url
        return dict(
            url=masked,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            ssl_mode=self.db_ssl_mode,
            env=self.api_env,
        )


@lru_cache(maxsize=1)
def get_db_config() -> DatabaseConfig:
    """
    Returns a cached DatabaseConfig instance.
    Call get_db_config.cache_clear() to reset in tests.
    """
    return DatabaseConfig()


# Module-level singleton for convenience
db_config = get_db_config()
