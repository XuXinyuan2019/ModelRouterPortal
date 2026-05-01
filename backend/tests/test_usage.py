"""Tests for usage tracking, balance deduction, and dashboard endpoints."""

import pytest
from httpx import AsyncClient

from app.database import Base
from app.models.usage import UsageRecord
from app.models.user import User
from app.models.activation import UserModelActivation
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


async def test_simulate_usage_success(async_client: AsyncClient, auth_headers: dict):
    """POST /api/v1/usage/simulate should deduct balance and record usage."""
    # Give user some balance and activate a model
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "testuser").first()
        assert user is not None
        user.balance = 100.0
        db.add(UserModelActivation(user_id=user.id, model_id="qwen3.6-plus", status="active"))
        db.commit()
    finally:
        db.close()

    resp = await async_client.post(
        "/api/v1/usage/simulate",
        headers=auth_headers,
        json={"model_id": "qwen3.6-plus", "tokens_input": 1000, "tokens_output": 500},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cost"] > 0
    assert data["new_balance"] < 100.0
    assert data["usage_record_id"] > 0

    # Verify usage record exists
    db = TestingSessionLocal()
    try:
        record = db.query(UsageRecord).filter(UsageRecord.id == data["usage_record_id"]).first()
        assert record is not None
        assert record.tokens_input == 1000
        assert record.tokens_output == 500
        assert record.cost == data["cost"]
    finally:
        db.close()


async def test_simulate_usage_insufficient_balance(async_client: AsyncClient, auth_headers: dict):
    """POST /api/v1/usage/simulate should return 402 when balance is zero."""
    # Activate model but keep balance at 0
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "testuser").first()
        assert user is not None
        user.balance = 0.0
        db.add(UserModelActivation(user_id=user.id, model_id="qwen3.6-plus", status="active"))
        db.commit()
    finally:
        db.close()

    resp = await async_client.post(
        "/api/v1/usage/simulate",
        headers=auth_headers,
        json={"model_id": "qwen3.6-plus", "tokens_input": 1000, "tokens_output": 500},
    )
    assert resp.status_code == 402


async def test_simulate_usage_model_not_activated(async_client: AsyncClient, auth_headers: dict):
    """POST /api/v1/usage/simulate should return 403 when model is not activated."""
    # Give balance but don't activate model
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "testuser").first()
        assert user is not None
        user.balance = 100.0
        db.commit()
    finally:
        db.close()

    resp = await async_client.post(
        "/api/v1/usage/simulate",
        headers=auth_headers,
        json={"model_id": "qwen3.6-plus", "tokens_input": 1000, "tokens_output": 500},
    )
    assert resp.status_code == 403


async def test_dashboard_with_usage(async_client: AsyncClient, auth_headers: dict):
    """Dashboard should reflect recorded usage."""
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "testuser").first()
        assert user is not None
        user.balance = 100.0
        db.add(UserModelActivation(user_id=user.id, model_id="qwen3.6-plus", status="active"))
        db.commit()
    finally:
        db.close()

    # Simulate a usage call
    resp = await async_client.post(
        "/api/v1/usage/simulate",
        headers=auth_headers,
        json={"model_id": "qwen3.6-plus", "tokens_input": 1000, "tokens_output": 500},
    )
    assert resp.status_code == 200
    simulate_data = resp.json()

    # Check dashboard
    resp = await async_client.get("/api/v1/dashboard/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cost_30d"] == simulate_data["cost"]
    assert data["total_requests_30d"] == 1
    assert data["balance"] == simulate_data["new_balance"]


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
