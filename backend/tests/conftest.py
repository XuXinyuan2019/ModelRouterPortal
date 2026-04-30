"""
Shared test fixtures for ModelRouter Portal backend tests.

Uses an in-memory SQLite database so every test session starts with a clean slate.
httpx.AsyncClient + ASGITransport drives requests through the real FastAPI app
without needing a running server.
"""

from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from httpx import ASGITransport, AsyncClient

from app.database import Base
from app.dependencies import get_db
from app.models.model import Model
from app.routes.models import SEED_MODELS

# ── ensure all ORM models are imported so Base.metadata is complete ──
import app.models  # noqa: F401


# ---------------------------------------------------------------------------
# Database engine & session (in-memory SQLite, sync)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite://"  # in-memory

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Yield a test-scoped database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# App fixture — override dependencies, create/drop tables per session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Create all tables once for the entire test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    """
    Truncate every table between tests so each test starts with a clean DB.
    Seed models are re-inserted after truncation.
    """
    yield
    # After each test, delete all rows
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()


@pytest.fixture(scope="session")
def app():
    """
    Return the FastAPI application with the DB dependency overridden.
    We import `app` from main *after* tables are created so the lifespan
    init_db() call is harmless (tables already exist).
    """
    from app.main import app as _app

    _app.dependency_overrides[get_db] = override_get_db
    yield _app
    _app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Mock Alibaba Cloud client creation
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_create_cloud_client():
    """
    Mock create_cloud_client so tests don't need real Alibaba Cloud credentials.
    Every registered test user automatically gets client_id=12345.
    """
    with patch("app.routes.auth.create_cloud_client") as mock:
        mock.return_value = {"id": 12345, "client_uuid": "mock-uuid-12345"}
        yield


# ---------------------------------------------------------------------------
# Seed models helper
# ---------------------------------------------------------------------------

def _seed_models() -> None:
    """Insert the four default models into the test database."""
    db = TestingSessionLocal()
    try:
        if db.query(Model).count() == 0:
            for m in SEED_MODELS:
                db.add(Model(**m))
            db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def seed_models():
    """Ensure seed models exist before every test."""
    _seed_models()


# ---------------------------------------------------------------------------
# Async HTTP client
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def async_client(app):
    """httpx AsyncClient that talks to the FastAPI app via ASGI transport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_user(async_client: AsyncClient):
    """
    Register a normal test user and return a dict with token + user info.
    """
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": "TestPass123!"},
    )
    assert resp.status_code == 200, f"Register failed: {resp.text}"
    data = resp.json()

    # Fetch user profile
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me_resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    user_info = me_resp.json()

    return {
        "token": data["access_token"],
        "user": user_info,
    }


@pytest_asyncio.fixture
async def admin_user(async_client: AsyncClient):
    """
    Register a user, then promote to admin directly in the database.
    Returns dict with token + user info.
    """
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"username": "adminuser", "password": "AdminPass123!"},
    )
    assert resp.status_code == 200, f"Register admin failed: {resp.text}"
    data = resp.json()

    # Promote to admin in DB
    from app.models.user import User

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "adminuser").first()
        assert user is not None
        user.is_admin = True
        db.commit()
    finally:
        db.close()

    # Fetch user profile (will now show is_admin=True)
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me_resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    user_info = me_resp.json()

    return {
        "token": data["access_token"],
        "user": user_info,
    }


@pytest_asyncio.fixture
async def auth_headers(test_user: dict) -> dict:
    """Authorization headers for the normal test user."""
    return {"Authorization": f"Bearer {test_user['token']}"}


@pytest_asyncio.fixture
async def admin_headers(admin_user: dict) -> dict:
    """Authorization headers for the admin user."""
    return {"Authorization": f"Bearer {admin_user['token']}"}
