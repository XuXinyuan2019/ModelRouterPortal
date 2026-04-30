"""Integration tests for /api/v1/auth endpoints."""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------

async def test_register_success(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "password": "StrongPass1!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_username(async_client: AsyncClient):
    # Register first time
    await async_client.post(
        "/api/v1/auth/register",
        json={"username": "dupuser", "password": "StrongPass1!"},
    )
    # Register again with same username
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"username": "dupuser", "password": "AnotherPass1!"},
    )
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

async def test_login_success(async_client: AsyncClient):
    # Setup: register user first
    await async_client.post(
        "/api/v1/auth/register",
        json={"username": "loginuser", "password": "LoginPass1!"},
    )
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "loginuser", "password": "LoginPass1!"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(async_client: AsyncClient):
    await async_client.post(
        "/api/v1/auth/register",
        json={"username": "wrongpwuser", "password": "CorrectPass1!"},
    )
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "wrongpwuser", "password": "WrongPass999!"},
    )
    assert resp.status_code == 401


async def test_login_nonexistent_user(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "ghost", "password": "NoOne123!"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------

async def test_get_me_authenticated(async_client: AsyncClient, auth_headers: dict):
    resp = await async_client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testuser"
    assert "id" in data
    assert "is_active" in data


async def test_get_me_no_token(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/auth/me")
    assert resp.status_code == 401  # HTTPBearer auto_error=True -> 401 (no credentials)


async def test_get_me_invalid_token(async_client: AsyncClient):
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401
