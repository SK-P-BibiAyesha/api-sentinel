
from pathlib import Path

import yaml


BASE_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = BASE_DIR / "samples"


def load_api(filename):
    file_path = SAMPLES_DIR / filename

    with file_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


from backend.comparator import compare_apis, compare_specs


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
