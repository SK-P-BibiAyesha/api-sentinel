
from pathlib import Path

import yaml

from backend.compatibility_rules import evaluate_compatibility_rule


BASE_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = BASE_DIR / "samples"


# Maps report labels to compatibility rule identifiers.
CHANGE_TYPE_MAP = {
    "Endpoint removed": "endpoint_removed",
    "Endpoint added": "endpoint_added",
    "HTTP method removed": "http_method_removed",
    "HTTP method added": "http_method_added",
    "Response field removed": "response_field_removed",
    "Response field added": "response_field_added",
    "Response field type changed": "response_field_type_changed",
    "Response enum restricted": "enum_values_restricted",
    "Response enum expanded": "enum_values_added",
    "Request parameter removed": "request_parameter_removed",
    "Optional request parameter added": "request_parameter_added_optional",
    "Required request parameter added": "request_parameter_added_required",
    "Request parameter became required": "request_parameter_became_required",
    "Request parameter became optional": "request_parameter_became_optional",
    "Request parameter type changed": "parameter_type_changed",
    "Request parameter enum restricted": "enum_values_restricted",
    "Request parameter enum expanded": "enum_values_expanded",
    "Request field removed": "request_field_removed",
    "Optional request field added": "request_field_added_optional",
    "Required request field added": "request_field_added_required",
    "Request field became required": "request_field_became_required",
    "Request field became optional": "request_field_became_optional",
    "Request field type changed": "request_field_type_changed",
    "Request field enum restricted": "enum_values_restricted",
    "Request field enum expanded": "enum_values_expanded",
    "Success response removed": "success_status_code_removed",
    "Success response added": "success_status_code_added",
    "Error response removed": "error_status_code_removed",
    "Error response added": "error_status_code_added",
}


def load_api(filename):
    """Load a YAML API specification from the samples directory."""
    file_path = SAMPLES_DIR / filename

    with file_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def add_finding(findings, severity, change, location, details):
    """Append a finding using the existing report structure."""
    findings.append({
        "severity": severity,
        "change": change,
        "location": location,
        "details": details,
    })


def get_json_schema(container):
    """Get a JSON schema from an application/json content definition."""
    if not isinstance(container, dict):
        return {}

    content = container.get("content", {})
    if not isinstance(content, dict):
        return {}

    json_content = content.get("application/json", {})
    if not isinstance(json_content, dict):
        return {}

    schema = json_content.get("schema", {})
    return schema if isinstance(schema, dict) else {}


def get_response_schema(operation, status_code="200"):
    """Get the schema for a particular response status code."""
    responses = operation.get("responses", {})
    response = responses.get(status_code, {})

    if not isinstance(response, dict):
        return {}

    return get_json_schema(response)


def collect_parameters(path_item, operation):
    """
    Collect path-level and operation-level parameters.

    Operation-level parameters override path-level parameters with
    the same (name, in) identity.
    """
    parameters = {}

    for parameter in path_item.get("parameters", []) or []:
        if isinstance(parameter, dict):
            key = (parameter.get("name"), parameter.get("in"))
            parameters[key] = parameter

    for parameter in operation.get("parameters", []) or []:
        if isinstance(parameter, dict):
            key = (parameter.get("name"), parameter.get("in"))
            parameters[key] = parameter

    return parameters


def compare_enum(old_enum, new_enum):
    """
    Return 'restricted', 'expanded', or None.

    An enum change is evaluated only when both schemas explicitly
    declare enum lists.
    """
    if not isinstance(old_enum, list) or not isinstance(new_enum, list):
        return None

    old_values = set(map(str, old_enum))
    new_values = set(map(str, new_enum))

    if old_values == new_values:
        return None

    if not old_values.issubset(new_values):
        return "restricted"

    if not new_values.issubset(old_values):
        return "expanded"

    return "restricted"


def compare_parameters(old_operation, new_operation, old_path_item,
                       new_path_item, location, findings):
    """Detect request parameter additions, removals and changes."""
    old_parameters = collect_parameters(old_path_item, old_operation)
    new_parameters = collect_parameters(new_path_item, new_operation)

    for key, old_parameter in old_parameters.items():
        name, parameter_location = key
        label = f"{parameter_location} parameter '{name}'"

        if key not in new_parameters:
            add_finding(
                findings, "REVIEW", "Request parameter removed",
                location,
                f"The {label} was removed.",
            )
            continue

        new_parameter = new_parameters[key]

        old_required = bool(old_parameter.get("required", False))
        new_required = bool(new_parameter.get("required", False))

        if not old_required and new_required:
            add_finding(
                findings, "BREAKING", "Request parameter became required",
                location,
                f"The {label} is now required.",
            )
        elif old_required and not new_required:
            add_finding(
                findings, "INFO", "Request parameter became optional",
                location,
                f"The {label} is now optional.",
            )

        old_schema = old_parameter.get("schema", {})
        new_schema = new_parameter.get("schema", {})

        old_type = old_schema.get("type")
        new_type = new_schema.get("type")

        if old_type != new_type and old_type is not None and new_type is not None:
            add_finding(
                findings, "BREAKING", "Request parameter type changed",
                location,
                f"The {label} changed type from '{old_type}' to '{new_type}'.",
            )

        enum_change = compare_enum(
            old_schema.get("enum"), new_schema.get("enum")
        )

        if enum_change == "restricted":
            add_finding(
                findings, "BREAKING", "Request parameter enum restricted",
                location,
                f"Allowed values for the {label} were restricted.",
            )
        elif enum_change == "expanded":
            add_finding(
                findings, "INFO", "Request parameter enum expanded",
                location,
                f"Additional values are allowed for the {label}.",
            )

    for key, new_parameter in new_parameters.items():
        if key in old_parameters:
            continue

        name, parameter_location = key
        required = bool(new_parameter.get("required", False))

        if required:
            change = "Required request parameter added"
            severity = "BREAKING"
        else:
            change = "Optional request parameter added"
            severity = "INFO"

        add_finding(
            findings,
            severity,
            change,
            location,
            f"{parameter_location} parameter '{name}' was added.",
        )


def compare_request_body(old_operation, new_operation, location, findings):
    """Detect changes to JSON request-body fields."""
    old_body = old_operation.get("requestBody", {})
    new_body = new_operation.get("requestBody", {})

    old_schema = get_json_schema(old_body)
    new_schema = get_json_schema(new_body)

    old_properties = old_schema.get("properties", {})
    new_properties = new_schema.get("properties", {})

    old_required = set(old_schema.get("required", []) or [])
    new_required = set(new_schema.get("required", []) or [])

    for field, old_definition in old_properties.items():
        if field not in new_properties:
            add_finding(
                findings, "REVIEW", "Request field removed", location,
                f"Request field '{field}' was removed.",
            )
            continue

        new_definition = new_properties[field]

        if field not in old_required and field in new_required:
            add_finding(
                findings, "BREAKING", "Request field became required",
                location,
                f"Request field '{field}' is now required.",
            )
        elif field in old_required and field not in new_required:
            add_finding(
                findings, "INFO", "Request field became optional",
                location,
                f"Request field '{field}' is now optional.",
            )

        old_type = old_definition.get("type")
        new_type = new_definition.get("type")

        if old_type != new_type and old_type is not None and new_type is not None:
            add_finding(
                findings, "BREAKING", "Request field type changed",
                location,
                f"Request field '{field}' changed type from "
                f"'{old_type}' to '{new_type}'.",
            )

        enum_change = compare_enum(
            old_definition.get("enum"), new_definition.get("enum")
        )

        if enum_change == "restricted":
            add_finding(
                findings, "BREAKING", "Request field enum restricted",
                location,
                f"Allowed values for request field '{field}' were restricted.",
            )
        elif enum_change == "expanded":
            add_finding(
                findings, "INFO", "Request field enum expanded",
                location,
                f"Additional values are allowed for request field '{field}'.",
            )

    for field in new_properties:
        if field in old_properties:
            continue

        if field in new_required:
            add_finding(
                findings, "BREAKING", "Required request field added",
                location,
                f"Required request field '{field}' was added.",
            )
        else:
            add_finding(
                findings, "INFO", "Optional request field added",
                location,
                f"Optional request field '{field}' was added.",
            )


def compare_response_statuses(old_operation, new_operation,
                              location, findings):
    """Detect added or removed numeric response status codes."""
    old_responses = old_operation.get("responses", {})
    new_responses = new_operation.get("responses", {})

    old_codes = {str(code) for code in old_responses}
    new_codes = {str(code) for code in new_responses}

    for code in sorted(old_codes - new_codes):
        # Skip non-standard response keys such as 'default'.
        if len(code) != 3 or not code.isdigit():
            continue

        if code.startswith("2"):
            change = "Success response removed"
            severity = "BREAKING"
        else:
            change = "Error response removed"
            severity = "REVIEW"

        add_finding(
            findings, severity, change, location,
            f"Response status code {code} was removed.",
        )

    for code in sorted(new_codes - old_codes):
        if len(code) != 3 or not code.isdigit():
            continue

        if code.startswith("2"):
            change = "Success response added"
            severity = "REVIEW"
        else:
            change = "Error response added"
            severity = "INFO"

        add_finding(
            findings, severity, change, location,
            f"Response status code {code} was added.",
        )


def compare_response_fields(old_operation, new_operation,
                            location, findings):
    """Compare response properties in the HTTP 200 JSON schema."""
    old_schema = get_response_schema(old_operation)
    new_schema = get_response_schema(new_operation)

    old_properties = old_schema.get("properties", {})
    new_properties = new_schema.get("properties", {})

    for field in old_properties:
        if field not in new_properties:
            add_finding(
                findings, "BREAKING", "Response field removed",
                location,
                f"Field '{field}' was removed.",
            )
            continue

        old_definition = old_properties[field]
        new_definition = new_properties[field]

        old_type = old_definition.get("type")
        new_type = new_definition.get("type")

        if old_type != new_type and old_type is not None and new_type is not None:
            add_finding(
                findings, "BREAKING", "Response field type changed",
                location,
                f"Field '{field}' changed from '{old_type}' to '{new_type}'.",
            )

        enum_change = compare_enum(
            old_definition.get("enum"), new_definition.get("enum")
        )

        if enum_change == "restricted":
            add_finding(
                findings, "BREAKING", "Response enum restricted",
                location,
                f"Allowed response values for '{field}' were restricted.",
            )
        elif enum_change == "expanded":
            add_finding(
                findings, "REVIEW", "Response enum expanded",
                location,
                f"New response values were added for '{field}'.",
            )

    for field in new_properties:
        if field not in old_properties:
            add_finding(
                findings, "INFO", "Response field added",
                location,
                f"Field '{field}' was added.",
            )


def compare_apis(old_api, new_api):
    findings = []

    old_paths = old_api.get("paths", {})
    new_paths = new_api.get("paths", {})

    # Detect removed and added endpoints.
    for path, methods in old_paths.items():
        if path not in new_paths:
            findings.append({
                "severity": "BREAKING",
                "change": "Endpoint removed",
                "location": path,
                "details": "This endpoint existed in the old API."
            })
            continue

        for method, operation in methods.items():
            new_operation = new_paths[path].get(method)

            if new_operation is None:
                findings.append({
                    "severity": "BREAKING",
                    "change": "HTTP method removed",
                    "location": f"{method.upper()} {path}",
                    "details": "This operation no longer exists."
                })
                continue

            old_schema = (
                operation.get("responses", {})
                .get("200", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
            )

            new_schema = (
                new_operation.get("responses", {})
                .get("200", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
            )

            old_properties = old_schema.get("properties", {})
            new_properties = new_schema.get("properties", {})

            # Detect removed response fields.
            for field in old_properties:
                if field not in new_properties:
                    findings.append({
                        "severity": "BREAKING",
                        "change": "Response field removed",
                        "location": f"{method.upper()} {path}",
                        "details": f"Field '{field}' was removed."
                    })

            # Detect new fields and changed data types.
            for field, new_definition in new_properties.items():
                if field not in old_properties:
                    findings.append({
                        "severity": "INFO",
                        "change": "Response field added",
                        "location": f"{method.upper()} {path}",
                        "details": f"Field '{field}' was added."
                    })
                    continue

                old_type = old_properties[field].get("type")
                new_type = new_definition.get("type")

                if old_type != new_type:
                    findings.append({
                        "severity": "BREAKING",
                        "change": "Response field type changed",
                        "location": f"{method.upper()} {path}",
                        "details": (
                            f"Field '{field}' changed from "
                            f"'{old_type}' to '{new_type}'."
                        )
                    })

    # Detect newly added endpoints.
    for path, methods in new_paths.items():
        if path not in old_paths:
            findings.append({
                "severity": "INFO",
                "change": "Endpoint added",
                "location": path,
                "details": "This endpoint was added in the new API."
            })
            continue

        for method in methods:
            if method not in old_paths[path]:
                findings.append({
                    "severity": "INFO",
                    "change": "HTTP method added",
                    "location": f"{method.upper()} {path}",
                    "details": "This operation was added."
                })

    return findings


def main():
    """Load the sample specifications, compare them, and print a report."""
    old_api = load_api("old-api.yaml")
    new_api = load_api("new-api.yaml")

    findings = compare_apis(old_api, new_api)

    breaking_count = sum(
        finding["severity"] == "BREAKING"
        for finding in findings
    )
    review_count = sum(
        finding["severity"] == "REVIEW"
        for finding in findings
    )

    print("\n=== API SENTINEL REPORT ===")
    print("Old version:", old_api["info"]["version"])
    print("New version:", new_api["info"]["version"])
    print("Total changes:", len(findings))
    print("Breaking changes:", breaking_count)
    print("Changes requiring review:", review_count)

    for number, finding in enumerate(findings, start=1):
        print(
            f"\n{number}. [{finding['severity']}] "
            f"{finding['change']}"
        )
        print("Location:", finding["location"])
        print("Details:", finding["details"])

        if "compatibility_title" in finding:
            print("Rule:", finding["compatibility_title"])
            print("Compatibility:", finding["compatibility_reason"])

    if breaking_count or review_count:
        print(
            "\nRESULT: FAIL - Resolve breaking changes and review "
            "uncertain changes before deployment."
        )
    else:
        print("\nRESULT: PASS - No breaking changes detected.")


if __name__ == "__main__":
    main()
