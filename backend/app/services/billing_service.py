"""Billing service — fetches pricing rules from Alibaba Cloud and calculates costs."""

import logging
from datetime import datetime
from typing import Any

from alibabacloud_aicontent20240611 import models as aicontent_models

from app.services.alicloud_client import get_alicloud_client

logger = logging.getLogger(__name__)

# In-memory cache for billing rules
_billing_rules_cache: dict[str, Any] | None = None
_cache_timestamp: datetime | None = None
_CACHE_TTL_SECONDS = 300

# Fallback pricing (¥ per 1M tokens, first tier) — matches Alibaba Cloud config
_FALLBACK_PRICING: dict[str, dict[str, Any]] = {
    "qwen3.6-plus": {
        "model_id": 1022,
        "tiers": [
            {"input_price": 2.0, "output_price": 12.0, "min_tokens": 0, "max_tokens": 256000},
            {"input_price": 8.0, "output_price": 48.0, "min_tokens": 256000, "max_tokens": 1000000},
        ],
    },
    "qwen3-max": {
        "model_id": 1023,
        "tiers": [
            {"input_price": 2.5, "output_price": 10.0, "min_tokens": 0, "max_tokens": 32000},
            {"input_price": 4.0, "output_price": 16.0, "min_tokens": 32000, "max_tokens": 128000},
            {"input_price": 7.0, "output_price": 28.0, "min_tokens": 128000, "max_tokens": 252000},
        ],
    },
    "kimi-k2.6": {
        "model_id": 1028,
        "tiers": [
            {"input_price": 6.5, "output_price": 27.0, "min_tokens": 0, "max_tokens": 0},
        ],
    },
    "deepseek-v4-pro": {
        "model_id": 1026,
        "tiers": [
            {"input_price": 12.0, "output_price": 24.0, "min_tokens": 0, "max_tokens": 0},
        ],
    },
}


def _parse_tier(tier: Any) -> dict[str, Any]:
    """Parse a single pricing tier from SDK response (dict or object)."""
    if isinstance(tier, dict):
        return {
            "input_price": float(tier.get("input_price", 0) or 0),
            "output_price": float(tier.get("output_price", 0) or 0),
            "min_tokens": int(tier.get("min_tokens", 0) or 0),
            "max_tokens": int(tier.get("max_tokens", 0) or 0),
        }
    return {
        "input_price": float(getattr(tier, "input_price", 0) or 0),
        "output_price": float(getattr(tier, "output_price", 0) or 0),
        "min_tokens": int(getattr(tier, "min_tokens", 0) or 0),
        "max_tokens": int(getattr(tier, "max_tokens", 0) or 0),
    }


def fetch_billing_rules() -> dict[str, dict[str, Any]]:
    """Fetch billing rules from Alibaba Cloud with in-memory caching.

    Returns dict keyed by modelCode (e.g. "qwen3.6-plus"), each value contains
    a "tiers" list with input_price/output_price/min_tokens/max_tokens per tier.
    """
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
            rules: dict[str, dict[str, Any]] = {}
            items = getattr(body.data, "list", []) or []
            for item in items:
                model_code = getattr(item, "model_code", None) or getattr(
                    item, "modelCode", None
                )
                if not model_code:
                    continue
                pricing_config = getattr(item, "pricing_config", None) or getattr(
                    item, "pricingConfig", None
                )
                if not pricing_config:
                    continue
                # pricing_config may be a dict or an SDK object
                if isinstance(pricing_config, dict):
                    tiers_raw = pricing_config.get("tiers", []) or []
                else:
                    tiers_raw = getattr(pricing_config, "tiers", []) or []
                if not tiers_raw:
                    continue
                tiers = [_parse_tier(t) for t in tiers_raw]
                model_id_val = getattr(item, "model_id", None) or getattr(item, "modelId", None)
                if tiers:
                    entry: dict[str, Any] = {"tiers": tiers}
                    if model_id_val is not None:
                        entry["model_id"] = int(model_id_val)
                    rules[str(model_code)] = entry
            if rules:
                _billing_rules_cache = rules
                _cache_timestamp = now
                logger.info("Loaded %d billing rules from Alibaba Cloud", len(rules))
                return rules
            logger.warning("Alibaba Cloud returned billing rules but parsing yielded no valid tiers")
    except Exception as e:
        logger.warning(
            "Failed to fetch billing rules from Alibaba Cloud, using fallback: %s", e
        )

    _billing_rules_cache = _FALLBACK_PRICING
    _cache_timestamp = now
    return _FALLBACK_PRICING


def get_billing_rule_for_model(model_id: str) -> dict[str, Any]:
    """Return pricing tiers for a specific model."""
    rules = fetch_billing_rules()
    return rules.get(model_id, {"tiers": []})


def calculate_cost(model_id: str, tokens_input: int, tokens_output: int) -> float:
    """Calculate cost based on model tiered pricing (per 1M tokens) and token counts.

    For models with multiple tiers, applies each tier's rate to the portion of
    tokens that falls within that tier's range.
    """
    rule = get_billing_rule_for_model(model_id)
    tiers = rule.get("tiers", [])
    if not tiers:
        return 0.0

    total_input_cost = 0.0
    total_output_cost = 0.0
    remaining_input = tokens_input
    remaining_output = tokens_output

    for tier in tiers:
        min_tok = tier.get("min_tokens", 0)
        max_tok = tier.get("max_tokens", 0)
        tier_capacity = (max_tok - min_tok) if max_tok > 0 else float("inf")

        # Input tokens in this tier
        if remaining_input > 0:
            input_in_tier = min(remaining_input, tier_capacity)
            total_input_cost += (input_in_tier / 1_000_000) * tier.get("input_price", 0)
            remaining_input -= input_in_tier

        # Output tokens in this tier
        if remaining_output > 0:
            output_in_tier = min(remaining_output, tier_capacity)
            total_output_cost += (output_in_tier / 1_000_000) * tier.get("output_price", 0)
            remaining_output -= output_in_tier

        if remaining_input <= 0 and remaining_output <= 0:
            break

    return round(total_input_cost + total_output_cost, 6)
