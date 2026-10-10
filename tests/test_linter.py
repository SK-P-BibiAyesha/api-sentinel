"""
Unit & Integration tests for linter.py (Member 2: Change Linter & Risk Analysis)
"""

import pytest
from backend.linter import analyze_changes, lint_changes


# --- 1. Test Single Breaking Change: Removed Response Field ---

def test_removed_response_field():
    """Verify response_field_removed is classified as breaking HIGH severity."""
    payload = {
        "changes": [
            {
                "change_type": "response_field_removed",
                "path": "/users/200/name",
                "location": "response",
                "old_value": {"type": "string"},
                "new_value": None,
            }
        ]
    }
    report = analyze_changes(payload)

    assert len(report["issues"]) == 1
    issue = report["issues"][0]
    assert issue["change_type"] == "response_field_removed"
    assert issue["path"] == "/users/200/name"
    assert issue["breaking"] is True
    assert issue["severity"] == "HIGH"
    assert issue["review_required"] is False
    assert "restore" in issue["recommendation"].lower()
    assert issue["location"] == "response"
    assert issue["old_value"] == {"type": "string"}
    assert issue["new_value"] is None

    # Verify summary
    assert report["summary"]["high"] == 1
    assert report["summary"]["critical"] == 0
    assert report["summary"]["medium"] == 0
    assert report["summary"]["low"] == 0
    assert report["review_required"] == 0


# --- 2. Test Safe Non-Breaking Change: Response Field Added ---

def test_safe_response_field_addition():
    """Verify response_field_added is classified as non-breaking LOW severity."""
    payload = {
        "changes": [
            {
                "change_type": "response_field_added",
                "path": "/users/200/avatar_url",
                "location": "response",
                "new_value": {"type": "string"},
            }
        ]
    }
    report = analyze_changes(payload)

    assert len(report["issues"]) == 1
    issue = report["issues"][0]
    assert issue["change_type"] == "response_field_added"
    assert issue["path"] == "/users/200/avatar_url"
    assert issue["breaking"] is False
    assert issue["severity"] == "LOW"
    assert issue["review_required"] is False
    assert "compatible" in issue["recommendation"].lower()

    # Verify summary
    assert report["summary"]["low"] == 1
    assert report["summary"]["critical"] == 0
    assert report["summary"]["high"] == 0
    assert report["summary"]["medium"] == 0
    assert report["review_required"] == 0


# --- 3. Test Multiple Changes in One Input ---

def test_multiple_changes_in_one_input():
    """Verify multiple heterogeneous changes are aggregated accurately."""
    payload = {
        "changes": [
            {"change_type": "endpoint_removed", "path": "/api/v1/auth/login"},
            {"change_type": "response_field_removed", "path": "/api/v1/users"},
            {"change_type": "enum_values_restricted", "path": "/api/v1/status"},
            {"change_type": "response_field_added", "path": "/api/v1/products"},
            {"change_type": "description_changed", "path": "/api/v1/health"},
        ]
    }
    report = analyze_changes(payload)

    assert len(report["issues"]) == 5
    assert report["summary"]["critical"] == 1
    assert report["summary"]["high"] == 1
    assert report["summary"]["medium"] == 1
    assert report["summary"]["low"] == 2
    assert report["review_required"] == 0


# --- 4. Test Empty Changes ---

@pytest.mark.parametrize("empty_payload", [
    {"changes": []},
    {},
    [],
])
def test_empty_changes(empty_payload):
    """Verify empty changes payload produces empty report without crashing."""
    report = analyze_changes(empty_payload)

    assert report["issues"] == []
    assert report["summary"] == {"critical": 0, "high": 0, "medium": 0, "low": 0}
    assert report["review_required"] == 0


# --- 5. Test Unknown Change Types ---

def test_unknown_change_types_require_manual_review():
    """Verify unknown changes are marked UNCLASSIFIED and never labeled safe."""
    payload = {
        "changes": [
            {
                "change_type": "custom_vendor_protocol_modified",
                "path": "/api/v1/custom",
            }
        ]
    }
    report = analyze_changes(payload)

    assert len(report["issues"]) == 1
    issue = report["issues"][0]
    assert issue["change_type"] == "custom_vendor_protocol_modified"
    assert issue["breaking"] is None
    assert issue["severity"] == "UNCLASSIFIED"
    assert issue["review_required"] is True
    assert "manual review" in issue["recommendation"].lower()

    # Unknown changes do not increment critical/high/medium/low
    assert report["summary"]["critical"] == 0
    assert report["summary"]["high"] == 0
    assert report["summary"]["medium"] == 0
    assert report["summary"]["low"] == 0
    assert report["review_required"] == 1


# --- 6. Test Malformed Inputs ---

@pytest.mark.parametrize("malformed_payload", [
    None,
    "not_a_dictionary_or_list",
    12345,
    {"changes": "not_a_list"},
    {"changes": None},
])
def test_malformed_top_level_payload(malformed_payload):
    """Verify malformed top-level payloads are handled gracefully."""
    report = analyze_changes(malformed_payload)

    assert len(report["issues"]) == 1
    assert report["issues"][0]["change_type"] == "invalid_input"
    assert report["issues"][0]["review_required"] is True
    assert report["review_required"] == 1


def test_malformed_individual_change_items():
    """Verify non-dictionary items in changes array are caught safely."""
    payload = {
        "changes": [
            "string_instead_of_dict",
            None,
            {"change_type": "endpoint_removed", "path": "/api/v1/users"},
        ]
    }
    report = analyze_changes(payload)

    assert len(report["issues"]) == 3
    assert report["issues"][0]["change_type"] == "invalid_input"
    assert report["issues"][0]["review_required"] is True
    assert report["issues"][1]["change_type"] == "invalid_input"
    assert report["issues"][1]["review_required"] is True
    assert report["issues"][2]["change_type"] == "endpoint_removed"
    assert report["issues"][2]["breaking"] is True

    assert report["summary"]["critical"] == 1
    assert report["review_required"] == 2


# --- 7. Test Summary Counts Calculation ---

def test_correct_summary_counts():
    """Verify strict mathematical accuracy of summary counts."""
    payload = {
        "changes": [
            {"change_type": "endpoint_removed"},  # Critical
            {"change_type": "http_method_removed"},  # High
            {"change_type": "request_parameter_became_required"},  # High
            {"change_type": "enum_values_restricted"},  # Medium
            {"change_type": "response_field_added"},  # Low
            {"change_type": "unknown_drift_event"},  # Unclassified (review_required)
        ]
    }
    report = analyze_changes(payload)

    assert report["summary"]["critical"] == 1
    assert report["summary"]["high"] == 2
    assert report["summary"]["medium"] == 1
    assert report["summary"]["low"] == 1
    assert report["review_required"] == 1


# --- 8. Test Function Alias ---

def test_pipeline_alias():
    """Verify lint_changes is an identical alias to analyze_changes."""
    payload = {"changes": [{"change_type": "endpoint_removed"}]}
    assert lint_changes(payload) == analyze_changes(payload)

