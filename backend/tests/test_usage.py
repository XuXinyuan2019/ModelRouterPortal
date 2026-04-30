"""Tests for usage and dashboard endpoints."""

from httpx import AsyncClient


async def test_usage_overview(async_client: AsyncClient, auth_headers: dict):
    """GET /api/v1/usage/overview should return 200 with usage data."""
    resp = await async_client.get("/api/v1/usage/overview", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_cost" in data
    assert "total_tokens" in data
    assert "total_requests" in data
    assert "period" in data


async def test_usage_trend(async_client: AsyncClient, auth_headers: dict):
    """GET /api/v1/usage/trend should return 200 with trend data list."""
    resp = await async_client.get("/api/v1/usage/trend", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


async def test_usage_models(async_client: AsyncClient, auth_headers: dict):
    """GET /api/v1/usage/models should return 200 with model usage list."""
    resp = await async_client.get("/api/v1/usage/models", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


async def test_dashboard(async_client: AsyncClient, auth_headers: dict):
    """GET /api/v1/dashboard/ should return 200 with balance + trend."""
    resp = await async_client.get("/api/v1/dashboard/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "balance" in data
    assert "recent_trend" in data
    assert "total_cost_30d" in data
    assert "total_requests_30d" in data
    assert "activated_models" in data
