"""
Recommendations Engine (Member 2: Change Linter & Risk Analysis)

This module generates deterministic, actionable remediation recommendations for
detected API schema changes. It guides engineers on how to preserve backward
compatibility or safely migrate consumers.

Severity calculation and recommendation generation are kept separate as independent concerns.
"""

from typing import Any, Dict, List, Optional, TypedDict

from backend.compatibility_rules import RuleResult
from backend.risk_engine import RiskResult


class RecommendationResult(TypedDict):
    """Normalized recommendation result structure."""
    change_type: str
    recommendation: str
    action_items: List[str]
    requires_manual_review: bool


# Deterministic recommendations catalog for supported change types
RECOMMENDATIONS_CATALOG: Dict[str, Dict[str, Any]] = {
    "endpoint_removed": {
        "recommendation": (
            "Restore the removed endpoint or introduce a versioned replacement (e.g., /v2) "
            "with a formal migration plan and client deprecation timeline."
        ),
        "action_items": [
            "Restore the endpoint path if existing clients are still active.",
            "Introduce a new versioned endpoint for updated functionality.",
            "Publish a deprecation timeline and migration guide before removing old paths.",
        ],
        "requires_manual_review": False,
    },
    "http_method_removed": {
        "recommendation": (
            "Restore the removed HTTP method or provide an alternative versioned endpoint "
            "supporting the operation to prevent HTTP 405 Method Not Allowed errors."
        ),
        "action_items": [
            "Restore the HTTP method handler on the current route.",
            "Provide an equivalent replacement route with clear migration docs.",
        ],
        "requires_manual_review": False,
    },
    "response_field_removed": {
        "recommendation": (
            "Restore the removed response field or implement a backward-compatible "
            "deprecation period with advance client notifications."
        ),
        "action_items": [
            "Retain the field in the response payload (can be populated with empty/null or marked deprecated).",
            "Audit downstream consumer dependencies before decommissioning fields.",
        ],
        "requires_manual_review": False,
    },
    "request_parameter_became_required": {
        "recommendation": (
            "Keep the request parameter optional or supply a safe server-side default "
            "value so legacy client requests do not fail schema validation."
        ),
        "action_items": [
            "Revert parameter requirement back to optional (required=false).",
            "Configure a sensible fallback default value on the server side.",
        ],
        "requires_manual_review": False,
    },
    "field_type_changed": {
        "recommendation": (
            "Preserve the original field data type, or introduce a new versioned field "
            "with the updated type to prevent client serialization and parsing failures."
        ),
        "action_items": [
            "Maintain original data type compatibility.",
            "Introduce a new distinct field (e.g., field_v2) if the type change is necessary.",
        ],
        "requires_manual_review": False,
    },
    "enum_values_restricted": {
        "recommendation": (
            "Retain previously accepted enum values where possible, or document a "
            "scheduled migration window before eliminating accepted values."
        ),
        "action_items": [
            "Restore the removed enum values in the schema contract.",
            "Provide a transition window and fallback handling for legacy values.",
        ],
        "requires_manual_review": False,
    },
    "response_field_added": {
        "recommendation": (
            "Adding an optional response field is generally backward-compatible, "
            "but verify that strict client deserializers do not reject unrecognized fields."
        ),
        "action_items": [
            "No structural compatibility fix is required for standard REST clients.",
            "Check strict client implementations to confirm they tolerate additional fields.",
        ],
        "requires_manual_review": False,
    },
    "description_changed": {
        "recommendation": (
            "Documentation and description updates do not alter functional schema behavior; "
            "no structural compatibility fix is usually required."
        ),
        "action_items": [
            "No structural code or schema fix needed.",
            "Ensure the updated description accurately communicates endpoint intent.",
        ],
        "requires_manual_review": False,
    },
}


def generate_recommendation(change_or_result: Any) -> RecommendationResult:
    """
    Generates actionable remediation recommendations for an API change or rule/risk result.

    Args:
        change_or_result: A dictionary representing a change, compatibility RuleResult,
                          or RiskResult. Must contain a 'change_type' key.

    Returns:
        RecommendationResult dictionary containing:
        - change_type: Evaluated change type string.
        - recommendation: Comprehensive guidance string.
        - action_items: List of concrete action steps.
        - requires_manual_review: Boolean indicating whether manual review is required.
    """
    # 1. Validate dictionary structure
    if not isinstance(change_or_result, dict):
        return {
            "change_type": "invalid_input",
            "recommendation": (
                "Invalid input format. Input must be a dictionary containing 'change_type'. "
                "Manual review is required."
            ),
            "action_items": ["Verify the input data format passed to the recommendations engine."],
            "requires_manual_review": True,
        }

    # 2. Check for empty dictionary
    if not change_or_result:
        return {
            "change_type": "missing_change_type",
            "recommendation": (
                "Empty change record provided. Manual review is required to evaluate remediation."
            ),
            "action_items": ["Provide a valid change dictionary containing 'change_type'."],
            "requires_manual_review": True,
        }

    # 3. Extract and validate change_type
    raw_change_type = change_or_result.get("change_type")
    if not isinstance(raw_change_type, str) or not raw_change_type.strip():
        return {
            "change_type": str(raw_change_type) if raw_change_type is not None else "missing_change_type",
            "recommendation": (
                "The 'change_type' field is missing or invalid. Manual review is required."
            ),
            "action_items": ["Ensure a non-empty string 'change_type' is provided in the input."],
            "requires_manual_review": True,
        }

    normalized_type = raw_change_type.strip()

    # 4. Check if compatibility breaking status was explicitly marked undetermined (None)
    if "breaking" in change_or_result and change_or_result["breaking"] is None:
        return {
            "change_type": normalized_type,
            "recommendation": (
                f"Compatibility impact for '{normalized_type}' is undetermined (breaking=None). "
                "Manual review is required before deploying this change."
            ),
            "action_items": [
                "Manually inspect the schema diff with API stakeholders.",
                "Confirm whether consumers can tolerate this modification.",
            ],
            "requires_manual_review": True,
        }

    # 5. Lookup recommendation in catalog
    entry = RECOMMENDATIONS_CATALOG.get(normalized_type)
    if entry is not None:
        return {
            "change_type": normalized_type,
            "recommendation": entry["recommendation"],
            "action_items": list(entry["action_items"]),
            "requires_manual_review": entry["requires_manual_review"],
        }

    # 6. Unknown change type: Never assume safe, recommend manual review
    return {
        "change_type": normalized_type,
        "recommendation": (
            f"Unrecognized change type '{normalized_type}'. Manual review is required with API "
            "stakeholders to determine appropriate remediation."
        ),
        "action_items": [
            "Conduct manual review of the API diff.",
            "Verify potential impact on downstream microservice consumers.",
        ],
        "requires_manual_review": True,
    }


# Convenient alias functions matching common nomenclature
get_recommendation = generate_recommendation
recommend_action = generate_recommendation

