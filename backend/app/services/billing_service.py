"""Billing service — fetches pricing rules from Alibaba Cloud and calculates costs."""

import logging
from datetime import datetime, timedelta
from typing import Any

from alibabacloud_aicontent20240611 import models as aicontent_models

from app.services.alicloud_client import get_alicloud_client

logger = logging.getLogger(__name__)

# In-memory cache for billing rules
_billing_rules_cache: dict[str, Any] | None = None
_cache_timestamp: datetime | None = None
_CACHE_TTL_SECONDS = 300

# Fallback mock pricing (¥ per 1M tokens) for development / testing
_FALLBACK_PRICING: dict[str, dict[str, float]] = {
    "qwen3.6-plus": {"input": 15.0, "output": 30.0},
    "qwen3-max": {"input": 20.0, "output": 40.0},
    "kimi-k2.6": {"input": 10.0, "output": 20.0},
    "deepseek-v4-pro": {"input": 5.0, "output": 15.0},
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
        req = aicontent_models.ModelRouterQueryBillingRuleListRequest()
        resp = client.model_router_query_billing_rule_list(req)
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
            # Only use Alibaba Cloud rules if they contain at least one known model
            # with non-zero pricing; otherwise fall back to local mock pricing
            known_models = set(_FALLBACK_PRICING.keys())
            has_known_model = any(
                mid in known_models and (r["input"] > 0 or r["output"] > 0)
                for mid, r in rules.items()
            )
            if has_known_model:
                _billing_rules_cache = rules
                _cache_timestamp = now
                logger.info("Loaded %d billing rules from Alibaba Cloud", len(rules))
                return rules
            logger.warning(
                "Alibaba Cloud returned %d billing rules but none match local models or have valid pricing, using fallback",
                len(rules),
            )
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
    """Calculate cost based on model pricing (per 1M tokens) and token counts."""
    rule = get_billing_rule_for_model(model_id)
    input_cost = (tokens_input / 1_000_000) * rule.get("input", 0)
    output_cost = (tokens_output / 1_000_000) * rule.get("output", 0)
    return round(input_cost + output_cost, 6)
