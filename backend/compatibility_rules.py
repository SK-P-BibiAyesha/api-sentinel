"""
Compatibility Rules Engine (Member 2: Change Linter & Risk Analysis)

This module evaluates API schema changes against deterministic backward-compatibility
rules. It classifies whether a detected drift is breaking or non-breaking.

Severity and recommendations are handled as separate concerns by downstream modules.
"""

from typing import Any, Dict, Optional, TypedDict


class RuleResult(TypedDict):
    """Normalized rule evaluation result."""
    change_type: str
    breaking: Optional[bool]
    title: str
    reason: str


# Rule registry for recognized change types
COMPATIBILITY_RULES: Dict[str, Dict[str, Any]] = {
    "endpoint_removed": {
        "breaking": True,
        "title": "Endpoint Removed",
        "reason": "An existing API endpoint was removed. Existing clients requesting this path will receive HTTP 404 Not Found errors.",
    },
    "http_method_removed": {
        "breaking": True,
        "title": "HTTP Method Removed",
        "reason": "An existing HTTP method was removed from an endpoint. Existing clients using this method will receive HTTP 405 Method Not Allowed.",
    },
    "response_field_removed": {
        "breaking": True,
        "title": "Response Field Removed",
        "reason": "A field was removed from an API response schema. Existing clients expecting this field may fail with parsing or key lookup errors.",
    },
    "request_parameter_became_required": {
        "breaking": True,
        "title": "Request Parameter Became Required",
        "reason": "A previously optional parameter is now required. Existing client requests omitting this parameter will fail with validation errors.",
    },
    "field_type_changed": {
        "breaking": True,
        "title": "Field Type Changed",
        "reason": "The data type of a request or response field changed. Existing clients will likely encounter type mismatch or deserialization errors.",
    },
    "enum_values_restricted": {
        "breaking": True,
        "title": "Enum Values Restricted",
        "reason": "Allowed enum values were restricted or removed. Existing clients transmitting or receiving removed values will fail validation.",
    },
    "response_field_added": {
        "breaking": False,
        "title": "Response Field Added",
        "reason": "A new field was added to an API response schema. Backward-compatible clients are expected to ignore unrecognized fields.",
    },
    "description_changed": {
        "breaking": False,
        "title": "Description Changed",
        "reason": "An API description or documentation string was modified. Schema structure and runtime behavior remain unchanged.",
    },
}


# Compatibility aliases for common change type synonyms
CHANGE_TYPE_ALIASES: Dict[str, str] = {
    "method_removed": "http_method_removed",
    "response_field_type_changed": "field_type_changed",
    "request_field_type_changed": "field_type_changed",
    "parameter_type_changed": "field_type_changed",
    "request_field_became_required": "request_parameter_became_required",
}


def evaluate_compatibility_rule(change: Any) -> RuleResult:
    """
    Evaluates an API change against backward-compatibility rules.

    Args:
        change: A dictionary representing a detected schema change.
                Must contain a 'change_type' string key.

    Returns:
        RuleResult dictionary containing:
        - change_type (str): The evaluated change type.
        - breaking (Optional[bool]): True for breaking, False for non-breaking,
                                     or None if unknown/invalid.
        - title (str): Human-readable title of the rule.
        - reason (str): Explanation of the backward-compatibility impact.
    """
    if not isinstance(change, dict):
        return {
            "change_type": "invalid_input",
            "breaking": None,
            "title": "Invalid Input Format",
            "reason": "Change record must be a dictionary. Manual review is required.",
        }

    raw_change_type = change.get("change_type")
    if not isinstance(raw_change_type, str) or not raw_change_type.strip():
        return {
            "change_type": str(raw_change_type) if raw_change_type is not None else "missing_change_type",
            "breaking": None,
            "title": "Invalid Change Type",
            "reason": "The 'change_type' key is missing, empty, or not a string. Manual review is required.",
        }

    normalized_type = raw_change_type.strip()
    canonical_type = CHANGE_TYPE_ALIASES.get(normalized_type, normalized_type)
    rule = COMPATIBILITY_RULES.get(canonical_type)

    if rule is not None:
        return {
            "change_type": normalized_type,
            "breaking": rule["breaking"],
            "title": rule["title"],
            "reason": rule["reason"],
        }

    # Unknown change type: Never assume safe! Require manual review.
    return {
        "change_type": normalized_type,
        "breaking": None,
        "title": "Unknown Change Type",
        "reason": f"Unrecognized change type '{normalized_type}'. Manual review is required to evaluate backward-compatibility impact.",
    }

