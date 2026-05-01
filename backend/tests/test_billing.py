"""Tests for billing service."""

import pytest
from app.services.billing_service import calculate_cost, get_billing_rule_for_model


def test_calculate_cost_with_known_model():
    """Cost calculation should use fallback pricing for known models."""
    cost = calculate_cost("qwen3.6-plus", tokens_input=1000, tokens_output=500)
    # input: 1000/1000 * 0.015 = 0.015
    # output: 500/1000 * 0.03 = 0.015
    assert cost == pytest.approx(0.03, abs=1e-6)


def test_calculate_cost_with_unknown_model():
    """Unknown models should default to zero cost."""
    cost = calculate_cost("unknown-model", tokens_input=1000, tokens_output=1000)
    assert cost == 0.0


def test_get_billing_rule_for_known_model():
    """Known model should return non-zero pricing."""
    rule = get_billing_rule_for_model("deepseek-v4-pro")
    assert "input" in rule
    assert "output" in rule
    assert rule["input"] > 0


def test_get_billing_rule_for_unknown_model():
    """Unknown model should return zero pricing."""
    rule = get_billing_rule_for_model("nonexistent")
    assert rule == {"input": 0.0, "output": 0.0}
