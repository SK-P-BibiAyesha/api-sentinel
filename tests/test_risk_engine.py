"""
Unit tests for risk_engine.py (Member 2: Change Linter & Risk Analysis)
"""

import pytest

from backend.compatibility_rules import evaluate_compatibility_rule
from backend.risk_engine import (
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_UNCLASSIFIED,
    classify_risk,
    classify_severity,
    evaluate_risk,
)


# --- 1. Tests for Known Severity Classifications ---

@pytest.mark.parametrize("change_type,expected_severity", [
    ("endpoint_removed", SEVERITY_CRITICAL),
    ("http_method_removed", SEVERITY_HIGH),
    ("response_field_removed", SEVERITY_HIGH),
    ("request_parameter_became_required", SEVERITY_HIGH),
    ("field_type_changed", SEVERITY_HIGH),
    ("enum_values_restricted", SEVERITY_MEDIUM),
    ("response_field_added", SEVERITY_LOW),
    ("description_changed", SEVERITY_LOW),
])
def test_known_change_severities(change_type, expected_severity):
    """Verify that every known change type maps to its documented deterministic severity level."""
    # Determine expected breaking boolean based on severity heuristic
    is_breaking = expected_severity in (SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM)
    rule_result = {
        "change_type": change_type,
        "breaking": is_breaking,
        "title": "Some Rule Title",
        "reason": "Some Rule Reason",
    }
    risk = classify_risk(rule_result)

    assert risk["change_type"] == change_type
    assert risk["severity"] == expected_severity
    assert risk["breaking"] is is_breaking
    assert risk["requires_manual_review"] is False
    assert isinstance(risk["reason"], str) and len(risk["reason"]) > 0


# --- 2. End-to-End Pipeline Integration with compatibility_rules ---

@pytest.mark.parametrize("change_dict,expected_severity,expected_breaking", [
    ({"change_type": "endpoint_removed", "path": "/users"}, SEVERITY_CRITICAL, True),
    ({"change_type": "response_field_added", "path": "/users"}, SEVERITY_LOW, False),
    ({"change_type": "enum_values_restricted", "path": "/orders"}, SEVERITY_MEDIUM, True),
])
def test_pipeline_integration(change_dict, expected_severity, expected_breaking):
    """Verify end-to-end integration: evaluate_compatibility_rule -> classify_risk."""
    rule_result = evaluate_compatibility_rule(change_dict)
    risk_result = classify_risk(rule_result)

    assert risk_result["severity"] == expected_severity
    assert risk_result["breaking"] is expected_breaking
    assert risk_result["requires_manual_review"] is False


# --- 3. Tests for Unknown Changes & Breaking=None ---

def test_unknown_change_type_requires_manual_review():
    """Verify unrecognized changes return UNCLASSIFIED and flag manual review."""
    rule_result = {
        "change_type": "custom_xml_gateway_extension_added",
        "breaking": None,
        "title": "Unknown Change Type",
        "reason": "Unrecognized change type.",
    }
    risk = classify_risk(rule_result)

    assert risk["change_type"] == "custom_xml_gateway_extension_added"
    assert risk["severity"] == SEVERITY_UNCLASSIFIED
    assert risk["breaking"] is None
    assert risk["requires_manual_review"] is True
    assert "manual review" in risk["reason"].lower()


def test_breaking_none_on_known_type_requires_manual_review():
    """Verify that if breaking is None, certainty is never invented even for known types."""
    rule_result = {
        "change_type": "endpoint_removed",
        "breaking": None,  # Undetermined compatibility status
        "title": "Endpoint Removed",
        "reason": "Undetermined status",
    }
    risk = classify_risk(rule_result)

    assert risk["severity"] == SEVERITY_UNCLASSIFIED
    assert risk["requires_manual_review"] is True
    assert "manual review" in risk["reason"].lower()


# --- 4. Tests for Invalid and Empty Inputs ---

@pytest.mark.parametrize("invalid_input", [
    None,
    "not_a_dict",
    12345,
    ["endpoint_removed"],
])
def test_invalid_input_types(invalid_input):
    """Verify non-dictionary inputs are handled safely without crashing."""
    risk = classify_risk(invalid_input)

    assert risk["change_type"] == "invalid_input"
    assert risk["severity"] == SEVERITY_UNCLASSIFIED
    assert risk["requires_manual_review"] is True


def test_empty_dict_input():
    """Verify empty dictionary input returns UNCLASSIFIED with manual review."""
    risk = classify_risk({})

    assert risk["change_type"] == "missing_change_type"
    assert risk["severity"] == SEVERITY_UNCLASSIFIED
    assert risk["requires_manual_review"] is True


@pytest.mark.parametrize("invalid_change_dict", [
    {"breaking": True},
    {"change_type": ""},
    {"change_type": "   "},
    {"change_type": 123},
])
def test_invalid_or_missing_change_type_key(invalid_change_dict):
    """Verify invalid or whitespace change_type values return UNCLASSIFIED."""
    risk = classify_risk(invalid_change_dict)

    assert risk["severity"] == SEVERITY_UNCLASSIFIED
    assert risk["requires_manual_review"] is True


# --- 5. Tests for Alias Functions ---

def test_function_aliases():
    """Verify classify_severity and evaluate_risk behave identically to classify_risk."""
    rule_result = {"change_type": "endpoint_removed", "breaking": True}
    res1 = classify_risk(rule_result)
    res2 = classify_severity(rule_result)
    res3 = evaluate_risk(rule_result)

    assert res1 == res2 == res3

