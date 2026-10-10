
from pathlib import Path

import yaml


BASE_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = BASE_DIR / "samples"


def load_api(filename):
    file_path = SAMPLES_DIR / filename

    with file_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


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
    old_api = load_api("old-api.yaml")
    new_api = load_api("new-api.yaml")

    findings = compare_apis(old_api, new_api)

    print("\n=== API SENTINEL REPORT ===")
    print("Old version:", old_api["info"]["version"])
    print("New version:", new_api["info"]["version"])

    breaking_count = sum(
        item["severity"] == "BREAKING" for item in findings
    )

    print("Total changes:", len(findings))
    print("Breaking changes:", breaking_count)

    for number, finding in enumerate(findings, start=1):
        print(f"\n{number}. [{finding['severity']}] "
              f"{finding['change']}")
        print("Location:", finding["location"])
        print("Details:", finding["details"])

    if breaking_count:
        print("\nRESULT: FAIL - Review breaking changes before deployment.")
    else:
        print("\nRESULT: PASS - No breaking changes detected by these rules.")


if __name__ == "__main__":
    main()
