"""
Risk Engine (Member 2: Change Linter & Risk Analysis)

This module classifies the severity and risk level of API schema changes based on
the evaluation results produced by backend.compatibility_rules.

Severity Levels:
- CRITICAL: Severe breaking changes halting availability (e.g. removed endpoint).
- HIGH: Significant contract breaking changes (e.g. removed method/field, new required param).
- MEDIUM: Partial contract restrictions (e.g. restricted enum values).
- LOW: Non-breaking additive or informational changes (e.g. new field, doc change).
- UNCLASSIFIED: Explicit state for unknown or undetermined changes requiring manual review.

Downstream recommendations are kept separate from severity scoring.
"""

from typing import Any, Dict, Optional, TypedDict

from backend.compatibility_rules import RuleResult

# Canonical Severity Levels
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"
SEVERITY_UNCLASSIFIED = "UNCLASSIFIED"

VALID_SEVERITY_LEVELS = {
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
}


class RiskResult(TypedDict):
    """Normalized risk classification output."""
    change_type: str
    severity: str
    breaking: Optional[bool]
    requires_manual_review: bool
    reason: str


# Deterministic Severity Mapping for recognized change types
SEVERITY_RULES: Dict[str, Dict[str, str]] = {
    "endpoint_removed": {
        "severity": SEVERITY_CRITICAL,
        "reason": "Removing an endpoint halts service availability for all existing clients calling this route.",
    },
    "http_method_removed": {
        "severity": SEVERITY_HIGH,
        "reason": "Removing an HTTP method prevents clients from executing operations on an active endpoint.",
    },
    "response_field_removed": {
        "severity": SEVERITY_HIGH,
        "reason": "Removing a response field causes parsing or missing key errors in consuming clients.",
    },
    "request_parameter_became_required": {
        "severity": SEVERITY_HIGH,
        "reason": "Making an optional parameter mandatory breaks all existing requests that omit it.",
    },
    "field_type_changed": {
        "severity": SEVERITY_HIGH,
        "reason": "Changing a field data type causes deserialization and validation errors across client SDKs.",
    },
    "enum_values_restricted": {
        "severity": SEVERITY_MEDIUM,
        "reason": "Restricting enum values breaks client workflows relying on previously valid options.",
    },
    "response_field_added": {
        "severity": SEVERITY_LOW,
        "reason": "Adding a response field is backward-compatible for clients ignoring unrecognized fields.",
    },
    "description_changed": {
        "severity": SEVERITY_LOW,
        "reason": "Updating documentation text has zero functional impact on runtime API contracts.",
    },
}


def classify_risk(rule_result: Any) -> RiskResult:
    """
    Classifies the severity and risk of an API change based on its compatibility rule result.

    Args:
        rule_result: A dictionary produced by evaluate_compatibility_rule or matching RuleResult.
                     Expected to contain 'change_type' and 'breaking' fields.

    Returns:
        RiskResult dictionary containing:
        - change_type: The evaluated change type string.
        - severity: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', or 'UNCLASSIFIED'.
        - breaking: True, False, or None.
        - requires_manual_review: True if change is unknown, invalid, or undetermined; False otherwise.
        - reason: Explanation of the assigned severity.
    """
    # 1. Validate input structure
    if not isinstance(rule_result, dict):
        return {
            "change_type": "invalid_input",
            "severity": SEVERITY_UNCLASSIFIED,
            "breaking": None,
            "requires_manual_review": True,
            "reason": "Input must be a valid rule result dictionary. Manual review required.",
        }

    # Empty dictionary check
    if not rule_result:
        return {
            "change_type": "missing_change_type",
            "severity": SEVERITY_UNCLASSIFIED,
            "breaking": None,
            "requires_manual_review": True,
            "reason": "Rule result dictionary is empty. Manual review required.",
        }

    raw_change_type = rule_result.get("change_type")
    if not isinstance(raw_change_type, str) or not raw_change_type.strip():
        return {
            "change_type": str(raw_change_type) if raw_change_type is not None else "missing_change_type",
            "severity": SEVERITY_UNCLASSIFIED,
            "breaking": None,
            "requires_manual_review": True,
            "reason": "The 'change_type' field is missing or invalid. Manual review required.",
        }

    normalized_type = raw_change_type.strip()
    breaking = rule_result.get("breaking")

    # 2. Check if breaking status is undetermined / null
    # If breaking is None, do not invent certainty or assume safety!
    if breaking is None:
        return {
            "change_type": normalized_type,
            "severity": SEVERITY_UNCLASSIFIED,
            "breaking": None,
            "requires_manual_review": True,
            "reason": f"Compatibility impact for '{normalized_type}' is undetermined (breaking=None). Manual review required.",
        }

    # 3. Look up severity heuristic
    rule_heuristic = SEVERITY_RULES.get(normalized_type)
    if rule_heuristic is not None:
        return {
            "change_type": normalized_type,
            "severity": rule_heuristic["severity"],
            "breaking": breaking,
            "requires_manual_review": False,
            "reason": rule_heuristic["reason"],
        }

    # 4. Unknown change type: Explicit unclassified result
    return {
        "change_type": normalized_type,
        "severity": SEVERITY_UNCLASSIFIED,
        "breaking": breaking,
        "requires_manual_review": True,
        "reason": f"Unrecognized change type '{normalized_type}'. Manual review required.",
    }


# Convenient alias functions matching common nomenclature
classify_severity = classify_risk
evaluate_risk = classify_risk

