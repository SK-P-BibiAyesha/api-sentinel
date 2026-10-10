"""
Unit tests for recommendations.py (Member 2: Change Linter & Risk Analysis)
"""

import pytest

from backend.compatibility_rules import evaluate_compatibility_rule
from backend.risk_engine import classify_risk
from backend.recommendations import (
    generate_recommendation,
    get_recommendation,
    recommend_action,
)


# --- 1. Tests for Supported Change Types ---

def test_endpoint_removed_recommendation():
    """Verify recommendation suggests restoring or versioned replacement with migration plan."""
    result = generate_recommendation({"change_type": "endpoint_removed", "breaking": True})

    assert result["change_type"] == "endpoint_removed"
    assert result["requires_manual_review"] is False
    rec_text = result["recommendation"].lower()
    assert "restore" in rec_text
    assert "versioned" in rec_text or "replacement" in rec_text
    assert "migration" in rec_text or "deprecation" in rec_text
    assert len(result["action_items"]) > 0


def test_http_method_removed_recommendation():
    """Verify recommendation suggests restoring method or providing replacement."""
    result = generate_recommendation({"change_type": "http_method_removed", "breaking": True})

    assert result["change_type"] == "http_method_removed"
    assert result["requires_manual_review"] is False
    rec_text = result["recommendation"].lower()
    assert "restore" in rec_text
    assert "replacement" in rec_text or "alternative" in rec_text


def test_response_field_removed_recommendation():
    """Verify recommendation suggests restoring field or backward-compatible deprecation period."""
    result = generate_recommendation({"change_type": "response_field_removed", "breaking": True})

    assert result["change_type"] == "response_field_removed"
    assert result["requires_manual_review"] is False
    rec_text = result["recommendation"].lower()
    assert "restore" in rec_text
    assert "deprecation" in rec_text


def test_request_parameter_became_required_recommendation():
    """Verify recommendation suggests keeping parameter optional or supplying safe default."""
    result = generate_recommendation({"change_type": "request_parameter_became_required", "breaking": True})

    assert result["change_type"] == "request_parameter_became_required"
    assert result["requires_manual_review"] is False
    rec_text = result["recommendation"].lower()
    assert "optional" in rec_text
    assert "default" in rec_text


def test_field_type_changed_recommendation():
    """Verify recommendation suggests preserving old type or introducing versioned field."""
    result = generate_recommendation({"change_type": "field_type_changed", "breaking": True})

    assert result["change_type"] == "field_type_changed"
    assert result["requires_manual_review"] is False
    rec_text = result["recommendation"].lower()
    assert "preserve" in rec_text or "original" in rec_text
    assert "versioned" in rec_text or "new" in rec_text


def test_enum_values_restricted_recommendation():
    """Verify recommendation suggests retaining old accepted values or documenting migration."""
    result = generate_recommendation({"change_type": "enum_values_restricted", "breaking": True})

    assert result["change_type"] == "enum_values_restricted"
    assert result["requires_manual_review"] is False
    rec_text = result["recommendation"].lower()
    assert "retain" in rec_text or "restore" in rec_text
    assert "migration" in rec_text or "window" in rec_text


def test_response_field_added_recommendation():
    """Verify recommendation notes general compatibility but cautions regarding strict clients."""
    result = generate_recommendation({"change_type": "response_field_added", "breaking": False})

    assert result["change_type"] == "response_field_added"
    assert result["requires_manual_review"] is False
    rec_text = result["recommendation"].lower()
    assert "compatible" in rec_text
    assert "strict" in rec_text


def test_description_changed_recommendation():
    """Verify recommendation notes no structural compatibility fix is required."""
    result = generate_recommendation({"change_type": "description_changed", "breaking": False})

    assert result["change_type"] == "description_changed"
    assert result["requires_manual_review"] is False
    rec_text = result["recommendation"].lower()
    assert "no structural" in rec_text or "no" in rec_text
    assert "fix" in rec_text or "unchanged" in rec_text


# --- 2. Tests for Unknown Changes & Undetermined Status ---

def test_unknown_change_type_requires_manual_review():
    """Verify unknown change types recommend manual review and do not claim safety."""
    result = generate_recommendation({"change_type": "custom_grpc_gateway_modified"})

    assert result["change_type"] == "custom_grpc_gateway_modified"
    assert result["requires_manual_review"] is True
    rec_text = result["recommendation"].lower()
    assert "manual review" in rec_text
    assert "safe" not in rec_text  # Must not claim it is safe


def test_breaking_none_requires_manual_review():
    """Verify that breaking=None flags manual review even for a known change type."""
    result = generate_recommendation({"change_type": "endpoint_removed", "breaking": None})

    assert result["requires_manual_review"] is True
    assert "manual review" in result["recommendation"].lower()


# --- 3. Tests for Malformed Input and Missing Fields ---

@pytest.mark.parametrize("malformed_input", [
    None,
    "not_a_dictionary",
    12345,
    ["endpoint_removed"],
])
def test_malformed_input_types(malformed_input):
    """Verify non-dictionary inputs are handled safely without crashing."""
    result = generate_recommendation(malformed_input)

    assert result["change_type"] == "invalid_input"
    assert result["requires_manual_review"] is True
    assert "manual review" in result["recommendation"].lower()


def test_empty_dict_input():
    """Verify empty dictionary input returns missing_change_type with manual review."""
    result = generate_recommendation({})

    assert result["change_type"] == "missing_change_type"
    assert result["requires_manual_review"] is True
    assert "manual review" in result["recommendation"].lower()


@pytest.mark.parametrize("invalid_dict", [
    {"breaking": True},
    {"change_type": ""},
    {"change_type": "   "},
    {"change_type": 123},
])
def test_missing_or_invalid_change_type_key(invalid_dict):
    """Verify missing, empty, or non-string change_type returns manual review."""
    result = generate_recommendation(invalid_dict)

    assert result["requires_manual_review"] is True
    assert "manual review" in result["recommendation"].lower()


# --- 4. End-to-End Pipeline Integration Test ---

def test_full_pipeline_integration():
    """Verify end-to-end integration across all 3 Member 2 modules."""
    raw_change = {"change_type": "endpoint_removed", "path": "/api/v1/auth/token"}

    rule_result = evaluate_compatibility_rule(raw_change)
    risk_result = classify_risk(rule_result)
    rec_result = generate_recommendation(risk_result)

    assert rule_result["breaking"] is True
    assert risk_result["severity"] == "CRITICAL"
    assert rec_result["requires_manual_review"] is False
    assert "restore" in rec_result["recommendation"].lower()


# --- 5. Tests for Function Aliases ---

def test_function_aliases():
    """Verify alias functions behave identically to generate_recommendation."""
    input_data = {"change_type": "endpoint_removed", "breaking": True}
    res1 = generate_recommendation(input_data)
    res2 = get_recommendation(input_data)
    res3 = recommend_action(input_data)

    assert res1 == res2 == res3

