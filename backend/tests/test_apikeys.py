"""Tests for API Key management endpoints."""

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from tests.conftest import TestingSessionLocal
from app.models.user import User


@pytest.fixture(autouse=True)
def _set_client_id_on_users():
    """
    After each test's user creation, ensure test users have a client_id
    so they pass the _get_client_id check in the apikeys route.
    We do this as a yield fixture: set client_id before test body runs
    only if users already exist (they won't at this point), so we also
    patch in each test as needed.
    """
    yield


def _set_user_client_id(username: str, client_id: int = 12345):
    """Helper: set client_id on a user in the test DB."""
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.client_id = client_id
            db.commit()
    finally:
        db.close()


MOCK_CREATE_RESULT = {
    "id": 1001,
    "api_key": "sk-test-1234567890abcdef",
    "client_id": 12345,
    "status": "active",
    "created_at": "2026-04-29T00:00:00",
}

MOCK_LIST_RESULT = [
    {
        "id": 1001,
        "api_key_preview": "sk-tes****cdef",
        "status": "active",
        "created_at": "2026-04-29T00:00:00",
    }
]


async def test_create_api_key(async_client: AsyncClient, test_user: dict):
    """POST /api/v1/api-keys/ should return 200 with full api_key."""
    _set_user_client_id("testuser")
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    with patch("app.routes.apikeys.apikey_service.create_api_key", return_value=MOCK_CREATE_RESULT):
        resp = await async_client.post("/api/v1/api-keys/", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert "api_key" in data
    assert data["api_key"] == "sk-test-1234567890abcdef"
    assert data["status"] == "active"
    assert data["id"] == 1001


async def test_list_api_keys(async_client: AsyncClient, test_user: dict):
    """GET /api/v1/api-keys/ should return 200 with masked api_key_preview."""
    _set_user_client_id("testuser")
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    with patch("app.routes.apikeys.apikey_service.list_api_keys", return_value=MOCK_LIST_RESULT):
        resp = await async_client.get("/api/v1/api-keys/", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    # Verify the key is masked (contains ****)
    assert "****" in data[0]["api_key_preview"]


async def test_delete_api_key(async_client: AsyncClient, test_user: dict):
    """DELETE /api/v1/api-keys/{id} should return 200."""
    _set_user_client_id("testuser")
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    with patch("app.routes.apikeys.apikey_service.delete_api_key", return_value=True):
        resp = await async_client.delete("/api/v1/api-keys/1001", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["detail"] == "API Key deleted"


async def test_create_key_without_auth(async_client: AsyncClient):
    """POST /api/v1/api-keys/ without auth should return 401 (no credentials)."""
    resp = await async_client.post("/api/v1/api-keys/")
    assert resp.status_code in (401, 403)


async def test_list_empty_keys(async_client: AsyncClient, test_user: dict):
    """GET /api/v1/api-keys/ should return 200 with empty list when no keys exist."""
    _set_user_client_id("testuser")
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    with patch("app.routes.apikeys.apikey_service.list_api_keys", return_value=[]):
        resp = await async_client.get("/api/v1/api-keys/", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data == []
