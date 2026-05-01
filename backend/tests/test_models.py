"""Integration tests for /api/v1/models endpoints."""

import pytest
from httpx import AsyncClient

MODEL_ID = "qwen3.6-plus"


# ---------------------------------------------------------------------------
# GET /models/
# ---------------------------------------------------------------------------

async def test_list_models(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/models/")
    assert resp.status_code == 200
    models = resp.json()
    assert isinstance(models, list)
    assert len(models) == 4
    model_ids = {m["model_id"] for m in models}
    assert MODEL_ID in model_ids


# ---------------------------------------------------------------------------
# GET /models/{model_id}
# ---------------------------------------------------------------------------

async def test_get_model_detail_public(async_client: AsyncClient):
    resp = await async_client.get(f"/api/v1/models/{MODEL_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_id"] == MODEL_ID
    assert "name" in data
    assert "provider" in data
    # Without auth, activated defaults to False
    assert data["activated"] is False


async def test_get_model_detail_with_auth(async_client: AsyncClient, auth_headers: dict):
    resp = await async_client.get(f"/api/v1/models/{MODEL_ID}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_id"] == MODEL_ID
    assert "activated" in data


async def test_get_model_not_found(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/models/nonexistent")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /models/{model_id}/activate
# ---------------------------------------------------------------------------

async def test_activate_model(async_client: AsyncClient, auth_headers: dict):
    resp = await async_client.post(
        f"/api/v1/models/{MODEL_ID}/activate", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"
    assert data["model_id"] == MODEL_ID


async def test_activate_already_active(async_client: AsyncClient, auth_headers: dict):
    # Activate first
    await async_client.post(
        f"/api/v1/models/{MODEL_ID}/activate", headers=auth_headers
    )
    # Try again
    resp = await async_client.post(
        f"/api/v1/models/{MODEL_ID}/activate", headers=auth_headers
    )
    assert resp.status_code == 409


async def test_activate_without_auth(async_client: AsyncClient):
    resp = await async_client.post(f"/api/v1/models/{MODEL_ID}/activate")
    assert resp.status_code == 401  # HTTPBearer auto_error -> 401 (no credentials)


# ---------------------------------------------------------------------------
# POST /models/{model_id}/deactivate
# ---------------------------------------------------------------------------

async def test_deactivate_model(async_client: AsyncClient, auth_headers: dict):
    # Activate first
    await async_client.post(
        f"/api/v1/models/{MODEL_ID}/activate", headers=auth_headers
    )
    # Deactivate
    resp = await async_client.post(
        f"/api/v1/models/{MODEL_ID}/deactivate", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "deactivated"


# ---------------------------------------------------------------------------
# GET /models/activated
# ---------------------------------------------------------------------------

async def test_list_activated_models(async_client: AsyncClient, auth_headers: dict):
    # Activate a model first
    await async_client.post(
        f"/api/v1/models/{MODEL_ID}/activate", headers=auth_headers
    )
    resp = await async_client.get("/api/v1/models/activated", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(a["model_id"] == MODEL_ID for a in data)
