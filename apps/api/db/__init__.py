from .database import (
    Base,
    get_db,
    get_db_session,
    check_db_health,
    get_engine,
    get_session_factory,
    init_schemas,
    create_all_tables,
)

# ---------------------------------------------------------------------------
# Backward-compatible lazy aliases
# Callers that do `from db import SessionLocal` or `from db import engine`
# will get the lazily-initialised singleton via module __getattr__.
# ---------------------------------------------------------------------------

def __getattr__(name: str):
    if name == "SessionLocal":
        return get_session_factory()
    if name == "engine":
        return get_engine()
    raise AttributeError(f"module 'db' has no attribute {name!r}")


__all__ = [
    "Base",
    "get_db",
    "get_db_session",
    "check_db_health",
    "get_engine",
    "get_session_factory",
    "init_schemas",
    "create_all_tables",
    # lazy aliases
    "SessionLocal",
    "engine",
]
