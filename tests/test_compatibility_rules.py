"""
Unit tests for compatibility_rules.py (Member 2: Change Linter & Risk Analysis)
"""

import pytest
from backend.compatibility_rules import evaluate_compatibility_rule


# --- 1. Tests for Recognized Breaking Changes ---

@pytest.mark.parametrize("change_type", [
    "endpoint_removed",
    "http_method_removed",
    "response_field_removed",
    "request_parameter_became_required",
    "field_type_changed",
    "enum_values_restricted",
])
def test_recognized_breaking_changes(change_type):
    """Verify that all destructive contract modifications are classified as breaking."""
    change = {"change_type": change_type, "path": "/users", "method": "GET"}
    result = evaluate_compatibility_rule(change)

    assert result["change_type"] == change_type
    assert result["breaking"] is True
    assert isinstance(result["title"], str) and len(result["title"]) > 0
    assert isinstance(result["reason"], str) and len(result["reason"]) > 0


# --- 2. Tests for Recognized Non-Breaking Changes ---

@pytest.mark.parametrize("change_type", [
    "response_field_added",
    "description_changed",
])
def test_recognized_non_breaking_changes(change_type):
    """Verify that additive and informational modifications are classified as non-breaking."""
    change = {"change_type": change_type, "path": "/users"}
    result = evaluate_compatibility_rule(change)

    assert result["change_type"] == change_type
    assert result["breaking"] is False
    assert isinstance(result["title"], str) and len(result["title"]) > 0
    assert isinstance(result["reason"], str) and len(result["reason"]) > 0


# --- 3. Tests for Unknown Change Types ---

def test_unknown_change_type():
    """Verify unknown change types return breaking=None and flag manual review."""
    change = {"change_type": "custom_vendor_extension_modified"}
    result = evaluate_compatibility_rule(change)

    assert result["change_type"] == "custom_vendor_extension_modified"
    assert result["breaking"] is None
    assert result["title"] == "Unknown Change Type"
    assert "manual review" in result["reason"].lower()


# --- 4. Tests for Invalid Inputs ---

@pytest.mark.parametrize("invalid_input", [
    None,
    "not_a_dictionary",
    12345,
    ["endpoint_removed"],
])
def test_invalid_input_types(invalid_input):
    """Verify non-dictionary inputs are handled safely without crashing."""
    result = evaluate_compatibility_rule(invalid_input)

    assert result["change_type"] == "invalid_input"
    assert result["breaking"] is None
    assert result["title"] == "Invalid Input Format"
    assert "manual review" in result["reason"].lower()


@pytest.mark.parametrize("invalid_dict", [
    {},
    {"path": "/users"},
    {"change_type": ""},
    {"change_type": "   "},
    {"change_type": 999},
])
def test_invalid_or_missing_change_type(invalid_dict):
    """Verify missing or non-string change_type returns breaking=None."""
    result = evaluate_compatibility_rule(invalid_dict)

    assert result["breaking"] is None
    assert result["title"] == "Invalid Change Type"
    assert "manual review" in result["reason"].lower()


def test_change_with_extra_metadata_preserves_evaluation():
    """Verify extraneous fields from drift detectors do not interfere with evaluation."""
    change = {
        "change_type": "endpoint_removed",
        "path": "/api/v1/orders",
        "method": "DELETE",
        "deprecated": False,
        "author": "Alice",
    }
    result = evaluate_compatibility_rule(change)

    assert result["change_type"] == "endpoint_removed"
    assert result["breaking"] is True

