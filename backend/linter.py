"""
Change Linter Integration Pipeline (Member 2: Change Linter & Risk Analysis)

This module unifies:
1. backend.compatibility_rules (contract breaking change detection)
2. backend.risk_engine (deterministic severity classification)
3. backend.recommendations (actionable remediation guidance)

It accepts structured schema diff changes and returns a comprehensive, normalized
linting report with summary statistics and manual review counters.
"""

from typing import Any, Dict, List, Optional, TypedDict

from backend.compatibility_rules import evaluate_compatibility_rule
from backend.risk_engine import (
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_UNCLASSIFIED,
    classify_risk,
)
from backend.recommendations import generate_recommendation


class SummaryCounts(TypedDict):
    """Aggregate severity counters."""
    critical: int
    high: int
    medium: int
    low: int


class LinterIssue(TypedDict, total=False):
    """Individual API drift issue report."""
    change_type: str
    path: Optional[str]
    breaking: Optional[bool]
    severity: Optional[str]
    title: str
    reason: str
    recommendation: str
    review_required: bool
    location: Optional[str]
    old_value: Any
    new_value: Any


class LinterReport(TypedDict):
    """Unified linter analysis report."""
    issues: List[LinterIssue]
    summary: SummaryCounts
    review_required: int


def analyze_changes(input_data: Any) -> LinterReport:
    """
    Analyzes API schema changes through the Member 2 triage pipeline.

    Args:
        input_data: A dictionary containing a 'changes' list, or directly a list of changes.
                    Example format:
                    {
                        "changes": [
                            {
                                "change_type": "response_field_removed",
                                "path": "/users/200/name",
                                "location": "response",
                                "old_value": {"type": "string"},
                                "new_value": None
                            }
                        ]
                    }

    Returns:
        LinterReport containing:
        - issues: List of normalized issue dictionaries with rule, severity, and recommendation data.
        - summary: Counts for critical, high, medium, and low severity issues.
        - review_required: Total count of issues requiring human/manual review.
    """
    summary: SummaryCounts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    # 1. Handle malformed top-level input
    if not isinstance(input_data, (dict, list)):
        malformed_issue: LinterIssue = {
            "change_type": "invalid_input",
            "path": None,
            "breaking": None,
            "severity": SEVERITY_UNCLASSIFIED,
            "title": "Invalid Input Format",
            "reason": "Top-level input must be a dictionary with a 'changes' list or a list of change records.",
            "recommendation": "Provide valid JSON/dictionary containing a 'changes' list.",
            "review_required": True,
        }
        return {
            "issues": [malformed_issue],
            "summary": summary,
            "review_required": 1,
        }

    # 2. Extract changes list
    if isinstance(input_data, list):
        raw_changes = input_data
    else:
        # Dictionary input
        if "changes" not in input_data:
            # Empty dict or missing 'changes' key
            return {
                "issues": [],
                "summary": summary,
                "review_required": 0,
            }
        raw_changes = input_data.get("changes")

    if not isinstance(raw_changes, list):
        malformed_issue = {
            "change_type": "invalid_input",
            "path": None,
            "breaking": None,
            "severity": SEVERITY_UNCLASSIFIED,
            "title": "Invalid Changes Payload",
            "reason": "The 'changes' field must be a list of change dictionaries.",
            "recommendation": "Ensure 'changes' is formatted as an array/list of change objects.",
            "review_required": True,
        }
        return {
            "issues": [malformed_issue],
            "summary": summary,
            "review_required": 1,
        }

    # 3. Process each change through the triage pipeline
    issues: List[LinterIssue] = []
    review_required_count = 0

    for raw_change in raw_changes:
        # Safeguard: Validate individual item is a dictionary
        if not isinstance(raw_change, dict):
            rule_res = evaluate_compatibility_rule(raw_change)
            risk_res = classify_risk(rule_res)
            rec_res = generate_recommendation(risk_res)

            issue: LinterIssue = {
                "change_type": "invalid_input",
                "path": None,
                "breaking": None,
                "severity": SEVERITY_UNCLASSIFIED,
                "title": "Invalid Change Record",
                "reason": "Individual change record must be a dictionary.",
                "recommendation": rec_res["recommendation"],
                "review_required": True,
            }
            issues.append(issue)
            review_required_count += 1
            continue

        # Step A: Rule Evaluation
        rule_res = evaluate_compatibility_rule(raw_change)

        # Step B: Severity Classification
        risk_res = classify_risk(rule_res)

        # Step C: Remediation Recommendation
        rec_res = generate_recommendation(risk_res)

        # Determine if manual review is required
        needs_review = (
            risk_res["requires_manual_review"]
            or rec_res["requires_manual_review"]
            or (rule_res["breaking"] is None)
        )

        issue = {
            "change_type": rule_res["change_type"],
            "path": raw_change.get("path"),
            "breaking": rule_res["breaking"],
            "severity": risk_res["severity"],
            "title": rule_res["title"],
            "reason": rule_res["reason"],
            "recommendation": rec_res["recommendation"],
            "review_required": needs_review,
        }

        # Preserve optional contextual details from diff if present
        if "location" in raw_change:
            issue["location"] = raw_change["location"]
        if "old_value" in raw_change:
            issue["old_value"] = raw_change["old_value"]
        if "new_value" in raw_change:
            issue["new_value"] = raw_change["new_value"]

        issues.append(issue)

        # Step D: Aggregate severity counters
        sev = risk_res["severity"]
        if sev == SEVERITY_CRITICAL:
            summary["critical"] += 1
        elif sev == SEVERITY_HIGH:
            summary["high"] += 1
        elif sev == SEVERITY_MEDIUM:
            summary["medium"] += 1
        elif sev == SEVERITY_LOW:
            summary["low"] += 1

        if needs_review:
            review_required_count += 1

    return {
        "issues": issues,
        "summary": summary,
        "review_required": review_required_count,
    }


# Convenient pipeline alias
lint_changes = analyze_changes

