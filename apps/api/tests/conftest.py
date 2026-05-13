"""Test fixtures for FlowSync API tests."""
from __future__ import annotations

import os
from typing import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only")
os.environ.setdefault("API_ENV", "test")

from db.database import Base, get_db
from main import app
from auth.models import AuthUser, Tenant
from auth.password import hash_password
from auth.jwt_handler import create_access_token


TEST_DB_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./test.db"
)

if "sqlite" in TEST_DB_URL:
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
else:
    engine = create_engine(TEST_DB_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create all tables once per session."""
    if "sqlite" in TEST_DB_URL:
        Base.metadata.create_all(bind=engine)
    else:
        with engine.begin() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS marts"))
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))
        Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Provide a transactional DB session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> TestClient:
    """FastAPI test client with DB override."""
    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_tenant(db: Session) -> Tenant:
    """Create a test tenant."""
    tenant = Tenant(
        id=uuid4(),
        name="Test Corp",
        slug="test-corp",
        plan="growth",
        is_active=True,
        max_users=10,
        max_api_keys=5,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def test_user(db: Session, test_tenant: Tenant) -> AuthUser:
    """Create a test user with owner role."""
    user = AuthUser(
        id=uuid4(),
        tenant_id=test_tenant.id,
        email="owner@testcorp.com",
        password_hash=hash_password("TestPass123!"),
        full_name="Test Owner",
        role="owner",
        is_active=True,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: AuthUser, test_tenant: Tenant) -> dict:
    """Generate valid JWT auth headers for the test user."""
    token = create_access_token(
        user_id=test_user.id,
        tenant_id=test_tenant.id,
        role=test_user.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_user(db: Session, test_tenant: Tenant) -> AuthUser:
    """Create a viewer-role user (limited permissions)."""
    user = AuthUser(
        id=uuid4(),
        tenant_id=test_tenant.id,
        email="viewer@testcorp.com",
        password_hash=hash_password("ViewerPass123!"),
        full_name="Test Viewer",
        role="viewer",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def viewer_headers(viewer_user: AuthUser, test_tenant: Tenant) -> dict:
    """JWT headers for viewer user."""
    token = create_access_token(
        user_id=viewer_user.id,
        tenant_id=test_tenant.id,
        role=viewer_user.role,
    )
    return {"Authorization": f"Bearer {token}"}
