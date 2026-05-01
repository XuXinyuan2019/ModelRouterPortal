"""Tests for account settings endpoints."""

from httpx import AsyncClient


async def test_change_password_success(async_client: AsyncClient, test_user: dict):
    """PUT /api/v1/settings/password should succeed and allow login with new password."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    resp = await async_client.put(
        "/api/v1/settings/password",
        json={"old_password": "TestPass123!", "new_password": "NewPass456!"},
        headers=headers,
    )
    assert resp.status_code == 200

    # Verify login with new password works
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "NewPass456!"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    # Verify old password no longer works
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "TestPass123!"},
    )
    assert resp.status_code == 401


async def test_change_password_wrong_old(async_client: AsyncClient, test_user: dict):
    """PUT /api/v1/settings/password with wrong old password should return 400."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    resp = await async_client.put(
        "/api/v1/settings/password",
        json={"old_password": "WrongOldPass!", "new_password": "NewPass456!"},
        headers=headers,
    )
    assert resp.status_code == 400


async def test_change_password_too_short(async_client: AsyncClient, test_user: dict):
    """PUT /api/v1/settings/password with short new password should return 422."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    resp = await async_client.put(
        "/api/v1/settings/password",
        json={"old_password": "TestPass123!", "new_password": "ab"},
        headers=headers,
    )
    assert resp.status_code == 422
