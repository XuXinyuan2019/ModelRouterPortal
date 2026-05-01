"""Tests for usage tracking and dashboard endpoints."""

from httpx import AsyncClient

from app.models.user import User
from tests.conftest import TestingSessionLocal


async def test_usage_overview_empty(async_client: AsyncClient, auth_headers: dict):
    """GET /api/v1/usage/overview should return zeros for new user."""
    resp = await async_client.get("/api/v1/usage/overview", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cost"] == 0.0
    assert data["total_tokens"] == 0
    assert data["total_requests"] == 0
    assert "period" in data


async def test_usage_trend_empty(async_client: AsyncClient, auth_headers: dict):
    """GET /api/v1/usage/trend should return empty list for new user."""
    resp = await async_client.get("/api/v1/usage/trend", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 0


async def test_usage_models_empty(async_client: AsyncClient, auth_headers: dict):
    """GET /api/v1/usage/models should return empty list for new user."""
    resp = await async_client.get("/api/v1/usage/models", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 0


async def test_dashboard_empty(async_client: AsyncClient, auth_headers: dict):
    """GET /api/v1/dashboard/ should return zeros for new user."""
    resp = await async_client.get("/api/v1/dashboard/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["balance"] == 0.0
    assert data["total_cost_30d"] == 0.0
    assert data["total_requests_30d"] == 0
    assert data["activated_models"] == 0
    assert data["recent_trend"] == []


async def test_balance_status(async_client: AsyncClient, auth_headers: dict):
    """GET /api/v1/balance/status should return balance and restriction flag."""
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "testuser").first()
        assert user is not None
        user.balance = 50.0
        db.commit()
    finally:
        db.close()

    resp = await async_client.get("/api/v1/balance/status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["balance"] == 50.0
    assert data["restricted"] is False

    # Set balance to zero and check again
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "testuser").first()
        assert user is not None
        user.balance = 0.0
        db.commit()
    finally:
        db.close()

    resp = await async_client.get("/api/v1/balance/status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["restricted"] is True
