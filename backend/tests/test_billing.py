"""Tests for billing service."""

import pytest
from app.services.billing_service import calculate_cost, get_billing_rule_for_model


def test_calculate_cost_with_known_model():
    """Cost calculation should use fallback pricing for known models (per 1M tokens)."""
    # qwen3.6-plus fallback: tier1 input=2, output=12 (0~256K tokens)
    cost = calculate_cost("qwen3.6-plus", tokens_input=1_000_000, tokens_output=500_000)
    # input: 1M tokens in tier1 (0~256K) + tier2 (256K~1M)
    # tier1: 256000/1M * 2 = 0.512
    # tier2: 744000/1M * 8 = 5.952
    # input total = 6.464
    # output: 500K all in tier1 (0~256K covers first 256K, rest in tier2)
    # tier1: 256000/1M * 12 = 3.072
    # tier2: 244000/1M * 48 = 11.712
    # output total = 14.784
    # grand total = 21.248
    assert cost == pytest.approx(21.248, abs=1e-4)


def test_calculate_cost_single_tier():
    """Single-tier model should use flat rate."""
    # kimi-k2.6 fallback: input=6.5, output=27 per 1M tokens
    cost = calculate_cost("kimi-k2.6", tokens_input=1_000_000, tokens_output=1_000_000)
    # input: 1M/1M * 6.5 = 6.5
    # output: 1M/1M * 27 = 27
    assert cost == pytest.approx(33.5, abs=1e-6)


def test_calculate_cost_with_unknown_model():
    """Unknown models should default to zero cost."""
    cost = calculate_cost("unknown-model", tokens_input=1_000_000, tokens_output=1_000_000)
    assert cost == 0.0


def test_get_billing_rule_for_known_model():
    """Known model should return tiers with non-zero pricing."""
    rule = get_billing_rule_for_model("deepseek-v4-pro")
    assert "tiers" in rule
    assert len(rule["tiers"]) > 0
    assert rule["tiers"][0]["input_price"] > 0
    assert rule["tiers"][0]["output_price"] > 0


def test_get_billing_rule_for_unknown_model():
    """Unknown model should return empty tiers."""
    rule = get_billing_rule_for_model("nonexistent")
    assert rule == {"tiers": []}
