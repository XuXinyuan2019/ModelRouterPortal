"""Tests for chat proxy endpoint."""

from unittest.mock import patch, MagicMock

from httpx import AsyncClient


async def test_chat_no_model(async_client: AsyncClient, auth_headers: dict):
    """POST /api/v1/chat/completions without model — 402 (zero balance) or 403."""
    resp = await async_client.post(
        "/api/v1/chat/completions",
        json={"model": "", "messages": [{"role": "user", "content": "hi"}]},
        headers=auth_headers,
    )
    assert resp.status_code in (402, 403, 422)


async def test_chat_model_not_activated(async_client: AsyncClient, test_user: dict):
    """POST /api/v1/chat/completions with non-activated model should return 403."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    from tests.conftest import TestingSessionLocal
    from app.models.user import User
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "testuser").first()
        user.balance = 100.0
        db.commit()
    finally:
        db.close()

    resp = await async_client.post(
        "/api/v1/chat/completions",
        json={"model": "qwen3.6-plus", "messages": [{"role": "user", "content": "hi"}]},
        headers=headers,
    )
    assert resp.status_code == 403
    detail = resp.json()["detail"].lower()
    assert "not activated" in detail or "未开通" in detail


async def test_chat_zero_balance(async_client: AsyncClient, test_user: dict):
    """POST /api/v1/chat/completions with zero balance should return 402."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    await async_client.post("/api/v1/models/qwen3.6-plus/activate", headers=headers)

    resp = await async_client.post(
        "/api/v1/chat/completions",
        json={"model": "qwen3.6-plus", "messages": [{"role": "user", "content": "hi"}]},
        headers=headers,
    )
    assert resp.status_code == 402


async def test_chat_no_api_key(async_client: AsyncClient, test_user: dict):
    """POST /api/v1/chat/completions when user has no API key should return 403."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    await async_client.post("/api/v1/models/qwen3.6-plus/activate", headers=headers)
    from tests.conftest import TestingSessionLocal
    from app.models.user import User
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "testuser").first()
        user.balance = 100.0
        db.commit()
    finally:
        db.close()

    # Mock apikey_service to return no keys
    with patch("app.routes.chat.apikey_service") as mock_ak:
        mock_ak.list_api_keys.return_value = []
        resp = await async_client.post(
            "/api/v1/chat/completions",
            json={"model": "qwen3.6-plus", "messages": [{"role": "user", "content": "hi"}]},
            headers=headers,
        )
        assert resp.status_code == 403
        assert "api key" in resp.json()["detail"].lower() or "API Key" in resp.json()["detail"]


async def test_chat_proxy_streaming(async_client: AsyncClient, test_user: dict):
    """POST /api/v1/chat/completions should proxy streaming via httpx with user API key."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    await async_client.post("/api/v1/models/qwen3.6-plus/activate", headers=headers)
    from tests.conftest import TestingSessionLocal
    from app.models.user import User
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.username == "testuser").first()
        user.balance = 100.0
        db.commit()
    finally:
        db.close()

    # Mock apikey_service to return a key
    with patch("app.routes.chat.apikey_service") as mock_ak:
        mock_ak.list_api_keys.return_value = [{"id": 1, "status": "active"}]
        mock_ak.copy_api_key.return_value = {"api_key": "sk-test-key-12345"}

        # Mock httpx.stream
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = iter([
            'data: {"choices":[{"delta":{"content":"Hello","reasoning_content":null},"index":0}]}',
            'data: {"choices":[{"delta":{"content":" world","reasoning_content":null},"index":0}]}',
            'data: {"choices":[],"usage":{"prompt_tokens":10,"completion_tokens":5}}',
            'data: [DONE]',
        ])

        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_response)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)

        with patch("app.routes.chat.httpx.stream", return_value=mock_stream_ctx):
            resp = await async_client.post(
                "/api/v1/chat/completions",
                json={"model": "qwen3.6-plus", "messages": [{"role": "user", "content": "hi"}], "stream": True},
                headers=headers,
            )
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")
