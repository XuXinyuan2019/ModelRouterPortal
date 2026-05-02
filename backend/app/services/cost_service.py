"""Cost service — wraps Alibaba Cloud Cost SDK APIs for real usage data."""

import logging
import time
from typing import Any

from alibabacloud_aicontent20240611 import models as aicontent_models

from app.services.alicloud_client import get_alicloud_client

logger = logging.getLogger(__name__)


def _days_to_ms(days: int) -> tuple[str, str]:
    """Return (start_ms, end_ms) for the last N days."""
    now = time.time()
    start = now - days * 86400
    return str(int(start * 1000)), str(int(now * 1000))


def _safe_to_map(obj: Any) -> Any:
    """Convert SDK response object to dict, handling lists and primitives."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, list):
        return [_safe_to_map(item) for item in obj]
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_map"):
        return obj.to_map()
    # Fallback: try to convert to dict
    try:
        return dict(obj)
    except Exception:
        return str(obj)


def get_cost_overview(client_id: int, days: int = 30) -> dict:
    """Get aggregated cost overview for a client."""
    start_ms, end_ms = _days_to_ms(days)
    try:
        client = get_alicloud_client()
        req = aicontent_models.ModelRouterQueryCostOverviewMetricsRequest(
            client_id=client_id,
            start_time=start_ms,
            end_time=end_ms,
        )
        resp = client.model_router_query_cost_overview_metrics(req)
        body = resp.body
        if not body or not body.success:
            return {"total_cost": 0.0, "total_tokens": 0, "total_requests": 0, "period": f"近{days}日"}

        data = _safe_to_map(body.data)
        if isinstance(data, list) and data:
            # Sum up from the list items
            total_cost = 0.0
            total_tokens = 0
            total_requests = 0
            for item in data:
                if isinstance(item, dict):
                    total_cost += float(item.get("total_amount", 0) or 0)
                    total_tokens += int(item.get("all_tokens", 0) or 0)
                    total_requests += int(item.get("total_calls", 0) or 0)
            return {
                "total_cost": round(total_cost, 4),
                "total_tokens": total_tokens,
                "total_requests": total_requests,
                "period": f"近{days}日",
            }
        return {"total_cost": 0.0, "total_tokens": 0, "total_requests": 0, "period": f"近{days}日"}
    except Exception as e:
        logger.warning("Failed to get cost overview: %s", e)
        return {"total_cost": 0.0, "total_tokens": 0, "total_requests": 0, "period": f"近{days}日"}


def get_cost_model_list(client_id: int, days: int = 30) -> list[dict]:
    """Get per-model cost breakdown for a client."""
    start_ms, end_ms = _days_to_ms(days)
    try:
        client = get_alicloud_client()
        req = aicontent_models.ModelRouterQueryCostModelListRequest(
            client_id=client_id,
            start_time=start_ms,
            end_time=end_ms,
        )
        resp = client.model_router_query_cost_model_list(req)
        body = resp.body
        if not body or not body.success:
            return []

        data = _safe_to_map(body.data)
        if not isinstance(data, dict):
            return []

        rows = data.get("rows", [])
        id_field = data.get("idField", "model_id")
        name_field = data.get("nameField", "model_code")

        result = []
        for row in rows:
            if isinstance(row, dict):
                result.append({
                    "model_id": str(row.get(id_field, "")),
                    "model_name": str(row.get(name_field, "")),
                    "cost": float(row.get("total_amount", 0) or 0),
                    "tokens": int(row.get("all_tokens", 0) or 0),
                    "requests": int(row.get("total_calls", 0) or 0),
                    "input_tokens": int(row.get("input_tokens", 0) or 0),
                    "output_tokens": int(row.get("output_tokens", 0) or 0),
                })
        return result
    except Exception as e:
        logger.warning("Failed to get cost model list: %s", e)
        return []


def get_cost_model_detail(
    client_id: int,
    model_id: int,
    days: int = 30,
    page_index: int = 1,
    page_size: int = 50,
) -> dict:
    """Get hourly/daily detail for a specific model."""
    start_ms, end_ms = _days_to_ms(days)
    try:
        client = get_alicloud_client()
        req = aicontent_models.ModelRouterQueryCostModelDetailRequest(
            client_id=client_id,
            model_id=model_id,
            start_time=start_ms,
            end_time=end_ms,
            page_index=page_index,
            page_size=page_size,
        )
        resp = client.model_router_query_cost_model_detail(req)
        body = resp.body
        if not body or not body.success:
            return {"rows": [], "total": 0, "page": page_index, "page_size": page_size}

        data = _safe_to_map(body.data)
        if not isinstance(data, dict):
            return {"rows": [], "total": 0, "page": page_index, "page_size": page_size}

        raw_rows = data.get("rows", [])
        rows = []
        for row in raw_rows:
            if isinstance(row, dict):
                rows.append({
                    "timestamp": row.get("timestamp", ""),
                    "total_calls": int(row.get("total_calls", 0) or 0),
                    "all_tokens": int(row.get("all_tokens", 0) or 0),
                    "input_tokens": int(row.get("input_tokens", 0) or 0),
                    "output_tokens": int(row.get("output_tokens", 0) or 0),
                    "reasoning_tokens": int(row.get("reasoning_tokens", 0) or 0),
                    "total_amount": float(row.get("total_amount", 0) or 0),
                })

        return {
            "rows": rows,
            "total": data.get("total", 0),
            "page": data.get("page", page_index),
            "page_size": data.get("pageSize", page_size),
            "model_id": data.get("modelId"),
            "model_name": data.get("modelName"),
            "granularity": data.get("granularity", "daily"),
        }
    except Exception as e:
        logger.warning("Failed to get cost model detail: %s", e)
        return {"rows": [], "total": 0, "page": page_index, "page_size": page_size}


def get_cost_trend(client_id: int, days: int = 7) -> list[dict]:
    """Get daily cost trend for a client."""
    start_ms, end_ms = _days_to_ms(days)
    try:
        client = get_alicloud_client()
        req = aicontent_models.ModelRouterQueryCostTrendMetricsRequest(
            client_id=client_id,
            start_time=start_ms,
            end_time=end_ms,
        )
        resp = client.model_router_query_cost_trend_metrics(req)
        body = resp.body
        if not body or not body.success:
            return []

        data = _safe_to_map(body.data)
        if isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, dict):
                    result.append({
                        "date": str(item.get("timestamp", "")),
                        "cost": float(item.get("total_amount", 0) or 0),
                        "tokens": int(item.get("all_tokens", 0) or 0),
                        "requests": int(item.get("total_calls", 0) or 0),
                    })
            return result
        return []
    except Exception as e:
        logger.warning("Failed to get cost trend: %s", e)
        return []
