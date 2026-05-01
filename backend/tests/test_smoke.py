"""Smoke tests to verify the test infrastructure works correctly."""


async def test_health_check(async_client):
    """The /api/v1/health endpoint should return 200."""
    resp = await async_client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_seed_models_available(async_client):
    """The model list endpoint should return the 4 seeded models."""
    resp = await async_client.get("/api/v1/models/")
    assert resp.status_code == 200
    models = resp.json()
    assert len(models) == 4
    model_ids = {m["model_id"] for m in models}
    assert "qwen3.6-plus" in model_ids
    assert "deepseek-v4-pro" in model_ids


async def test_register_and_login(async_client):
    """Register a user, then login with the same credentials."""
    # Register
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"username": "smokeuser", "password": "Smoke123!"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    # Login
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "smokeuser", "password": "Smoke123!"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_test_user_fixture(test_user):
    """The test_user fixture should provide a token and user info."""
    assert "token" in test_user
    assert "user" in test_user
    assert test_user["user"]["username"] == "testuser"


async def test_admin_user_fixture(admin_user):
    """The admin_user fixture should have is_admin=True."""
    assert admin_user["user"]["is_admin"] is True


async def test_auth_headers_fixture(async_client, auth_headers):
    """auth_headers should allow accessing protected endpoints."""
    resp = await async_client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


async def test_admin_headers_fixture(async_client, admin_headers):
    """admin_headers should allow accessing protected endpoints as admin."""
    resp = await async_client.get("/api/v1/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["is_admin"] is True
