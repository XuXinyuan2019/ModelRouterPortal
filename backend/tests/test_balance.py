"""Tests for balance and recharge endpoints."""

from httpx import AsyncClient


async def test_get_balance(async_client: AsyncClient, auth_headers: dict):
    """GET /api/v1/balance/ should return 200 with initial balance=0."""
    resp = await async_client.get("/api/v1/balance/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "balance" in data
    assert data["balance"] == 0.0


async def test_submit_recharge(async_client: AsyncClient, auth_headers: dict):
    """POST /api/v1/balance/recharge should return 200 with status=completed."""
    resp = await async_client.post(
        "/api/v1/balance/recharge",
        json={"amount": 100.0, "remark": "test recharge"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["amount"] == 100.0
    assert data["remark"] == "test recharge"
    assert data["balance_after"] == 100.0


async def test_recharge_invalid_amount(async_client: AsyncClient, auth_headers: dict):
    """POST /api/v1/balance/recharge with invalid amount should return 422."""
    # amount <= 0 violates gt=0 constraint
    resp = await async_client.post(
        "/api/v1/balance/recharge",
        json={"amount": -10.0},
        headers=auth_headers,
    )
    assert resp.status_code == 422

    # amount > 100000 violates le=100000 constraint
    resp = await async_client.post(
        "/api/v1/balance/recharge",
        json={"amount": 200000.0},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_recharge_history(async_client: AsyncClient, auth_headers: dict):
    """GET /api/v1/balance/history should return 200 with recharge records."""
    # First submit a recharge
    await async_client.post(
        "/api/v1/balance/recharge",
        json={"amount": 50.0},
        headers=auth_headers,
    )

    resp = await async_client.get("/api/v1/balance/history", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["amount"] == 50.0


async def test_admin_approve_recharge(
    async_client: AsyncClient,
    test_user: dict,
    admin_headers: dict,
):
    """Recharge now completes immediately; verify balance is updated."""
    user_headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Submit recharge as normal user — should complete immediately
    resp = await async_client.post(
        "/api/v1/balance/recharge",
        json={"amount": 200.0},
        headers=user_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["balance_after"] == 200.0

    # Verify balance updated
    resp = await async_client.get("/api/v1/balance/", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["balance"] == 200.0


async def test_non_admin_approve(
    async_client: AsyncClient,
    auth_headers: dict,
):
    """POST /api/v1/balance/recharge/{id}/approve as non-admin should return 403."""
    # Submit a recharge first
    resp = await async_client.post(
        "/api/v1/balance/recharge",
        json={"amount": 100.0},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    record_id = resp.json()["id"]

    # Try to approve as non-admin
    resp = await async_client.post(
        f"/api/v1/balance/recharge/{record_id}/approve",
        headers=auth_headers,
    )
    assert resp.status_code == 403
