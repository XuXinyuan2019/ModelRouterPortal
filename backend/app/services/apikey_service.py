"""API Key management service — wraps Alibaba Cloud SDK calls with mock fallback."""
import secrets
import time
from datetime import datetime

from alibabacloud_aicontent20240611 import models as aicontent_models

from app.config import settings
from app.services.alicloud_client import get_alicloud_client

# ---------- Mock storage (in-memory, per-process) ----------
_mock_store: dict[int, list[dict]] = {}


def _mock_api_key_id():
    return int(time.time() * 1000) % 10000000


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return key[:3] + "****"
    return key[:6] + "****" + key[-4:]


def create_api_key(client_id: int) -> dict:
    """Create an API Key for the given client. Returns dict with id, api_key, etc."""
    if settings.MOCK_MODE:
        key_value = f"sk-mock-{secrets.token_hex(24)}"
        record = {
            "id": _mock_api_key_id(),
            "api_key": key_value,
            "client_id": client_id,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        }
        _mock_store.setdefault(client_id, []).append(record)
        return record

    client = get_alicloud_client()
    req = aicontent_models.ModelRouterCreateApiKeyRequest(client_id=client_id)
    resp = client.model_router_create_api_key(req)
    body = resp.body
    if not body.success:
        raise Exception(body.err_message or "Failed to create API Key")
    data = body.data
    return {
        "id": getattr(data, "id", None),
        "api_key": getattr(data, "api_key", None),
        "client_id": client_id,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
    }


def list_api_keys(client_id: int) -> list[dict]:
    """List all API Keys for the given client."""
    if settings.MOCK_MODE:
        return [
            {
                "id": k["id"],
                "api_key_preview": _mask_key(k["api_key"]),
                "status": k["status"],
                "created_at": k["created_at"],
            }
            for k in _mock_store.get(client_id, [])
        ]

    client = get_alicloud_client()
    req = aicontent_models.ModelRouterQueryApiKeyListRequest(
        client_id=client_id,
        page_index=1,
        page_size=100,
    )
    resp = client.model_router_query_api_key_list(req)
    body = resp.body
    if not body.success:
        raise Exception(body.err_message or "Failed to list API Keys")
    items = body.data.list if body.data and body.data.list else []
    return [
        {
            "id": getattr(item, "id", None),
            "api_key_preview": _mask_key(getattr(item, "api_key", "")) if getattr(item, "api_key", None) else "sk-****",
            "status": getattr(item, "status", "active"),
            "created_at": getattr(item, "gmt_create", None),
        }
        for item in items
    ]


def delete_api_key(key_id: int, client_id: int) -> bool:
    """Delete an API Key by its ID."""
    if settings.MOCK_MODE:
        keys = _mock_store.get(client_id, [])
        _mock_store[client_id] = [k for k in keys if k["id"] != key_id]
        return True

    client = get_alicloud_client()
    resp = client.model_router_delete_api_key(key_id)
    body = resp.body
    if not body.success:
        raise Exception(body.err_message or "Failed to delete API Key")
    return True
