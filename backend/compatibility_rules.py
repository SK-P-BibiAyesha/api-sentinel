

"""

Compatibility Rules Engine

API Sentinel — Change Linter & Risk Analysis

Evaluates detected API schema changes against 100 deterministic rules.

Severity and recommendations are handled by downstream modules.

"""

from typing import Any, Dict, Optional, TypedDict

class RuleResult(TypedDict):

    """Normalized rule evaluation result."""

    change_type: str

    breaking: Optional[bool]

    title: str

    reason: str

# Each entry contains:

# change_type, breaking, title, reason

# breaking: True = breaking, False = non-breaking, None = review required.

_RULES = [

    # 1–10: Endpoints and operations

    ("endpoint_removed", True, "Endpoint Removed",

     "Existing clients calling this path may receive HTTP 404."),

    ("endpoint_added", False, "Endpoint Added",

     "A new path was added without removing existing endpoints."),

    ("http_method_removed", True, "HTTP Method Removed",

     "Clients using the removed method may receive HTTP 405."),

    ("http_method_added", False, "HTTP Method Added",

     "A new HTTP method is supported on an endpoint."),

    ("operation_id_changed", None, "Operation ID Changed",

     "Generated SDKs may rely on operationId; review client-generation impact."),

    ("operation_id_removed", None, "Operation ID Removed",

     "Generated SDKs may rely on operationId; review client-generation impact."),

    ("deprecated_operation_removed", True, "Deprecated Operation Removed",

     "Clients still using this operation will fail after removal."),

    ("summary_changed", False, "Summary Changed",

     "The operation summary changed without an identified schema change."),

    ("tag_removed", None, "Tag Removed",

     "Documentation grouping or generated SDK organization may change."),

    ("server_url_changed", None, "Server URL Changed",

     "Clients configured with the old base URL may need reconfiguration."),

    # 11–20: Request and response fields

    ("response_field_removed", True, "Response Field Removed",

     "Clients expecting the field may fail parsing or key lookup."),

    ("response_field_added", False, "Response Field Added",

     "Clients that tolerate unknown response fields should continue working."),

    ("response_field_became_required", None, "Response Field Became Required",

     "Output-field requiredness changed; review generated clients and consumers."),

    ("response_field_became_optional", False, "Response Field Became Optional",

     "Clients assuming the field always exists may fail when it is absent."),

    ("request_field_removed", None, "Request Field Removed",

     "Clients sending this field may experience changed behavior or validation."),

    ("request_field_added_optional", False, "Optional Request Field Added",

     "Existing requests can omit the new optional field."),

    ("request_field_added_required", True, "Required Request Field Added",

     "Requests omitting the new required field may fail validation."),

    ("request_field_became_required", True, "Request Field Became Required",

     "Requests omitting this field may now fail validation."),

    ("request_field_became_optional", False, "Request Field Became Optional",

     "Requests can omit a field that was previously required."),

    ("field_name_changed", True, "Field Name Changed",

     "Clients using the old property name may fail to find the value."),

    # 21–30: Types, nullability, and numeric constraints

    ("field_type_changed", True, "Field Type Changed",

     "Clients may encounter type mismatch or serialization errors."),

    ("request_field_type_changed", True, "Request Field Type Changed",

     "Existing request payloads may no longer validate."),

    ("response_field_type_changed", True, "Response Field Type Changed",

     "Clients may be unable to deserialize the changed response type."),

    ("field_format_changed", None, "Field Format Changed",

     "Format changes may affect validation or parsing; inspect the formats."),

    ("field_nullability_restricted", True, "Field Nullability Restricted",

     "Previously accepted null values may now be rejected."),

    ("field_nullability_relaxed", False, "Field Nullability Relaxed",

     "The schema now accepts null values in addition to prior values."),

    ("minimum_value_increased", True, "Minimum Value Increased",

     "Previously valid smaller values may now be rejected."),

    ("minimum_value_decreased", False, "Minimum Value Decreased",

     "The permitted numeric range has expanded downward."),

    ("maximum_value_decreased", True, "Maximum Value Decreased",

     "Previously valid larger values may now be rejected."),

    ("maximum_value_increased", False, "Maximum Value Increased",

     "The permitted numeric range has expanded upward."),

    # 31–40: Strings, enums, and arrays

    ("min_length_increased", True, "Minimum Length Increased",

     "Previously valid shorter strings may now be rejected."),

    ("min_length_decreased", False, "Minimum Length Decreased",

     "Shorter strings are now accepted."),

    ("max_length_decreased", True, "Maximum Length Decreased",

     "Previously valid longer strings may now be rejected."),

    ("max_length_increased", False, "Maximum Length Increased",

     "Longer strings are now accepted."),

    ("pattern_restricted", True, "Pattern Restricted",

     "Values accepted by the previous pattern may now be rejected."),

    ("pattern_relaxed", False, "Pattern Relaxed",

     "The accepted string pattern has broadened."),

    ("enum_values_restricted", True, "Enum Values Restricted",

     "Previously allowed enum values may now fail validation."),

    ("enum_values_expanded", False, "Enum Values Expanded",

     "Additional enum values are now allowed."),

    ("enum_values_removed", True, "Enum Values Removed",

     "Clients sending or receiving removed values may fail."),

    ("enum_values_added", None, "Enum Values Added",

     "New enum values may break exhaustive client handling; review consumers."),

    # 41–50: Arrays and objects

    ("array_item_type_changed", True, "Array Item Type Changed",

     "Clients may not parse array items using the previous type."),

    ("array_items_became_required", None, "Array Items Became Required",

     "Array item constraints changed; verify client and server expectations."),

    ("array_min_items_increased", True, "Minimum Array Items Increased",

     "Previously valid shorter arrays may now be rejected."),

    ("array_max_items_decreased", True, "Maximum Array Items Decreased",

     "Previously valid longer arrays may now be rejected."),

    ("array_unique_items_enabled", True, "Unique Array Items Required",

     "Arrays containing duplicate items may now be rejected."),

    ("object_additional_properties_restricted", True,

     "Additional Properties Restricted",

     "Objects containing extra properties may now fail validation."),

    ("object_additional_properties_allowed", False,

     "Additional Properties Allowed",

     "The schema now permits additional object properties."),

    ("nested_object_removed", True, "Nested Object Removed",

     "Clients relying on the nested object may fail."),

    ("nested_object_added", None, "Nested Object Added",

     "Impact depends on requiredness and how clients parse nested objects."),

    ("field_renamed", True, "Field Renamed",

     "Clients using the old field name may fail to find the value."),

    # 51–60: Parameters

    ("request_parameter_removed", None, "Request Parameter Removed",

     "Clients sending this parameter may experience changed behavior."),

    ("request_parameter_added_optional", False,

     "Optional Request Parameter Added",

     "Existing clients can continue without sending this parameter."),

    ("request_parameter_added_required", True,

     "Required Request Parameter Added",

     "Existing requests omitting the parameter may fail."),

    ("request_parameter_became_required", True,

     "Request Parameter Became Required",

     "Requests omitting this parameter may fail validation."),

    ("request_parameter_became_optional", False,

     "Request Parameter Became Optional",

     "Clients may omit a parameter that was previously required."),

    ("parameter_type_changed", True, "Parameter Type Changed",

     "Existing parameter values may no longer validate or parse."),

    ("parameter_location_changed", True, "Parameter Location Changed",

     "Clients sending the parameter in its old location may fail."),

    ("parameter_name_changed", True, "Parameter Name Changed",

     "Clients using the old parameter name may fail."),

    ("query_parameter_added", None, "Query Parameter Added",

     "Impact depends on whether the parameter is optional or required."),

    ("path_parameter_added", True, "Path Parameter Added",

     "Existing URLs may not match the new path template."),

    # 61–70: Headers, cookies, and request bodies

    ("path_parameter_removed", True, "Path Parameter Removed",

     "Existing URL templates may no longer match the endpoint."),

    ("header_parameter_added_required", True, "Required Header Added",

     "Clients not sending the new required header may fail."),

    ("header_parameter_removed", None, "Header Parameter Removed",

     "Clients or middleware relying on the header may be affected."),

    ("cookie_parameter_added_required", True, "Required Cookie Added",

     "Requests without the required cookie may fail."),

    ("request_body_added_required", True, "Required Request Body Added",

     "Clients that previously sent no body may fail."),

    ("request_body_became_optional", False, "Request Body Became Optional",

     "Clients can omit a body that was previously required."),

    ("request_body_removed", True, "Request Body Removed",

     "Clients sending a body may no longer be supported."),

    ("request_body_media_type_removed", True,

     "Request Body Media Type Removed",

     "Clients using the removed content type may fail."),

    ("request_body_media_type_added", False,

     "Request Body Media Type Added",

     "An additional request content type is accepted."),

    ("content_encoding_changed", None, "Content Encoding Changed",

     "Clients may need to adapt payload encoding or decoding."),

    # 71–80: Responses and content types

    ("response_removed", True, "Response Removed",

     "Clients may encounter an undocumented or unsupported response."),

    ("success_status_code_removed", True, "Success Status Code Removed",

     "Clients relying on the removed success code may mishandle responses."),

    ("success_status_code_added", None, "Success Status Code Added",

     "Clients may need to handle the additional success response code."),

    ("error_status_code_removed", None, "Error Status Code Removed",

     "Clients or monitoring relying on this error code may be affected."),

    ("error_status_code_added", False, "Error Status Code Added",

     "An additional error response is documented; clients should handle errors."),

    ("response_media_type_removed", True, "Response Media Type Removed",

     "Clients requesting the removed content type may fail."),

    ("response_media_type_added", False, "Response Media Type Added",

     "An additional response content type is supported."),

    ("response_content_type_changed", True, "Response Content Type Changed",

     "Clients expecting the previous content type may fail to parse responses."),

    ("response_schema_changed", None, "Response Schema Changed",

     "Inspect the detailed schema differences to determine compatibility."),

    ("request_schema_changed", None, "Request Schema Changed",

     "Inspect the detailed schema differences to determine compatibility."),

    # 81–90: Documentation, examples, and security

    ("response_example_changed", False, "Response Example Changed",

     "Only the example changed, assuming the schema and runtime are unchanged."),

    ("request_example_changed", False, "Request Example Changed",

     "Only the example changed, assuming the schema and runtime are unchanged."),

    ("description_changed", False, "Description Changed",

     "Documentation text changed without an identified structural change."),

    ("security_requirement_added", True, "Security Requirement Added",

     "Clients may need additional credentials or scopes."),

    ("security_requirement_removed", False, "Security Requirement Removed",

     "Fewer credentials may be required; review the intended security posture."),

    ("security_scheme_removed", True, "Security Scheme Removed",

     "Clients configured for the removed scheme may no longer authenticate."),

    ("security_scheme_added", False, "Security Scheme Added",

     "An additional authentication scheme is documented."),

    ("oauth_scope_added_required", True, "Required OAuth Scope Added",

     "Tokens without the required scope may be rejected."),

    ("oauth_scope_removed", None, "OAuth Scope Removed",

     "Authorization behavior may change; review server enforcement."),

    ("authentication_behavior_changed", True,

     "Authentication Behavior Changed",

     "Existing authentication flows may stop working."),

    # 91–100: Servers, operations, and runtime behavior

    ("server_url_removed", True, "Server URL Removed",

     "Clients using the removed server URL may be unable to reach the API."),

    ("server_url_added", False, "Server URL Added",

     "An additional server URL is available."),

    ("pagination_parameter_changed", None, "Pagination Parameter Changed",

     "Clients may need to update pagination requests."),

    ("default_value_changed", None, "Default Value Changed",

     "Behavior may change for requests that omit the value."),

    ("deprecated_flag_added", None, "Deprecated Flag Added",

     "The feature is marked for future removal but may still function."),

    ("rate_limit_reduced", True, "Rate Limit Reduced",

     "Previously valid traffic may receive throttling responses more often."),

    ("timeout_behavior_changed", None, "Timeout Behavior Changed",

     "Clients may observe different latency or timeout outcomes."),

    ("webhook_removed", True, "Webhook Removed",

     "Consumers relying on the webhook will stop receiving its events."),

    ("webhook_added", False, "Webhook Added",

     "A new webhook endpoint or event is available."),

    ("field_description_changed", False, "Field Description Changed",

     "Only field documentation changed; schema behavior is unchanged."),

]

# Build the public rule registry.

COMPATIBILITY_RULES: Dict[str, Dict[str, Any]] = {

    change_type: {

        "breaking": breaking,

        "title": title,

        "reason": reason,

    }

    for change_type, breaking, title, reason in _RULES

}

# Common change-type synonyms mapped to canonical rules.

CHANGE_TYPE_ALIASES: Dict[str, str] = {

    "method_removed": "http_method_removed",

    "method_added": "http_method_added",

    "response_field_type_changed": "field_type_changed",

    "request_field_type_changed": "field_type_changed",

    "parameter_type_changed": "field_type_changed",

    "request_field_became_required": "request_parameter_became_required",

    "request_parameter_required": "request_parameter_became_required",

    "request_parameter_optional": "request_parameter_became_optional",

    "response_field_deleted": "response_field_removed",

    "endpoint_deleted": "endpoint_removed",

    "endpoint_created": "endpoint_added",

    "field_deleted": "response_field_removed",

    "field_added": "response_field_added",

    "enum_restricted": "enum_values_restricted",

    "enum_expanded": "enum_values_expanded",

}

def evaluate_compatibility_rule(change: Any) -> RuleResult:

    """

    Evaluate a detected API schema change against the compatibility rules.

    Args:

        change: A dictionary containing a 'change_type' string key.

    Returns:

        RuleResult with:

          - change_type: the supplied normalized change type

          - breaking: True, False, or None when manual review is required

          - title: human-readable rule title

          - reason: explanation of the compatibility impact

    """

    if not isinstance(change, dict):

        return {

            "change_type": "invalid_input",

            "breaking": None,

            "title": "Invalid Input Format",

            "reason": (

                "Change record must be a dictionary. "

                "Manual review is required."

            ),

        }

    raw_change_type = change.get("change_type")

    if not isinstance(raw_change_type, str) or not raw_change_type.strip():

        return {

            "change_type": (

                str(raw_change_type)

                if raw_change_type is not None

                else "missing_change_type"

            ),

            "breaking": None,

            "title": "Invalid Change Type",

            "reason": (

                "The 'change_type' key is missing, empty, or not a string. "

                "Manual review is required."

            ),

        }

    normalized_type = raw_change_type.strip().lower()
    canonical_type = CHANGE_TYPE_ALIASES.get(
        normalized_type, normalized_type
    )

    rule = COMPATIBILITY_RULES.get(canonical_type)

    if rule is not None:

        return {

            "change_type": normalized_type,

            "breaking": rule["breaking"],

            "title": rule["title"],

            "reason": rule["reason"],

        }

    # Unknown changes must never be assumed safe.

    return {

        "change_type": normalized_type,

        "breaking": None,

        "title": "Unknown Change Type",

        "reason": (

            f"Unrecognized change type '{normalized_type}'. "

            "Manual review is required to evaluate backward compatibility."

        ),

    }

def get_compatibility_rule_count() -> int:

    """Return the number of registered canonical compatibility rules."""

    return len(COMPATIBILITY_RULES)

if __name__ == "__main__":

    print(

        "Registered compatibility rules:",

        get_compatibility_rule_count(),

    )

    sample_changes = [

        {"change_type": "endpoint_removed"},

        {"change_type": "response_field_added"},

        {"change_type": "enum_values_added"},

        {"change_type": "some_unknown_change"},

    ]

    for sample in sample_changes:

        print("\nInput:", sample)

        print("Result:", evaluate_compatibility_rule(sample))
