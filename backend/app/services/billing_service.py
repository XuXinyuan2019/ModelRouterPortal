"""Billing service — fetches pricing rules from Alibaba Cloud and calculates costs."""

import logging
from datetime import datetime, timedelta
from typing import Any

from app.services.alicloud_client import get_alicloud_client

logger = logging.getLogger(__name__)

# In-memory cache for billing rules
_billing_rules_cache: dict[str, Any] | None = None
_cache_timestamp: datetime | None = None
_CACHE_TTL_SECONDS = 300

# Fallback mock pricing (¥ per 1K tokens) for development / testing
_FALLBACK_PRICING: dict[str, dict[str, float]] = {
    "qwen3.6-plus": {"input": 0.015, "output": 0.03},
    "qwen3-max": {"input": 0.02, "output": 0.04},
    "kimi-k2.6": {"input": 0.01, "output": 0.02},
    "deepseek-v4-pro": {"input": 0.005, "output": 0.015},
}


def fetch_billing_rules() -> dict[str, dict[str, float]]:
    """Fetch billing rules from Alibaba Cloud with in-memory caching."""
    global _billing_rules_cache, _cache_timestamp

    now = datetime.utcnow()
    if (
        _billing_rules_cache
        and _cache_timestamp
        and (now - _cache_timestamp).seconds < _CACHE_TTL_SECONDS
    ):
        return _billing_rules_cache

    try:
        client = get_alicloud_client()
        resp = client.model_router_query_billing_rule_list()
        body = resp.body
        if body and body.success and body.data:
            rules: dict[str, dict[str, float]] = {}
            data = body.data
            items = getattr(data, "list", []) or []
            for item in items:
                model_id = getattr(item, "model_id", None) or getattr(
                    item, "modelId", None
                )
                if model_id:
                    rules[str(model_id)] = {
                        "input": float(getattr(item, "input_price", 0) or 0),
                        "output": float(getattr(item, "output_price", 0) or 0),
                    }
            if rules:
                _billing_rules_cache = rules
                _cache_timestamp = now
                logger.info("Loaded %d billing rules from Alibaba Cloud", len(rules))
                return rules
    except Exception as e:
        logger.warning(
            "Failed to fetch billing rules from Alibaba Cloud, using fallback: %s", e
        )

    _billing_rules_cache = _FALLBACK_PRICING
    _cache_timestamp = now
    return _FALLBACK_PRICING


def get_billing_rule_for_model(model_id: str) -> dict[str, float]:
    """Return pricing rule for a specific model."""
    rules = fetch_billing_rules()
    return rules.get(model_id, {"input": 0.0, "output": 0.0})


def calculate_cost(model_id: str, tokens_input: int, tokens_output: int) -> float:
    """Calculate cost based on model pricing and token counts."""
    rule = get_billing_rule_for_model(model_id)
    input_cost = (tokens_input / 1000) * rule.get("input", 0)
    output_cost = (tokens_output / 1000) * rule.get("output", 0)
    return round(input_cost + output_cost, 6)
