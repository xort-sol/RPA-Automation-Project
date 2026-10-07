"""
RPA-Based Automation
Irish Rental Property Application Process

Automates the STRUCTURED, RULE-BASED tasks of the process:
  Task 3  - Schedule viewing
  Task 7  - Validate required fields/documents
  Task 8  - Log application & assign reference number
  Task 9  - Verify tenant identity
  Task 13 - Run credit check
  Task 22 - Register tenancy with RTB
  Task 23 - Set up utility account transfers
  Task 26 - Archive application & close case

In a production deployment this logic would run inside UiPath (or Power
Automate) as a set of workflow activities calling real external systems
(credit bureau API, RTB e-tenancy portal, property management system).
Here the external systems are represented by mock functions so the
end-to-end pipeline can be demonstrated without live credentials.
"""

import json
import random
import string
import csv
from datetime import datetime, timedelta

REQUIRED_FIELDS = [
    "applicant_name", "pps_number", "monthly_income",
    "monthly_rent", "employment_letter", "id_document_valid"
]


# ---------------------------------------------------------------------------
# Mock external system connectors (would be real API/UI calls in production)
# ---------------------------------------------------------------------------

def mock_credit_bureau_api(pps_number: str) -> int:
    """Simulates a call to a credit reference agency API."""
    random.seed(pps_number)  # deterministic per applicant for demo purposes
    return random.randint(500, 900)


def mock_rtb_portal_submit(application: dict) -> str:
    """Simulates web-form submission to the RTB tenancy registration portal."""
    ref = "RTB-" + "".join(random.choices(string.digits, k=8))
    return ref


def mock_utility_provider_api(application: dict) -> str:
    """Simulates initiating a utility account transfer."""
    return f"UTIL-{application['app_id']}-TRANSFER-INITIATED"


# ---------------------------------------------------------------------------
# RPA workflow steps
# ---------------------------------------------------------------------------

def task3_schedule_viewing(applicant_name: str) -> dict:
    slot = datetime.now() + timedelta(days=random.randint(1, 5), hours=random.randint(9, 17))
    return {"applicant": applicant_name, "viewing_slot": slot.strftime("%Y-%m-%d %H:%M")}


def task7_validate_fields(application: dict) -> dict:
    missing = [f for f in REQUIRED_FIELDS if application.get(f) in (None, "")]
    passed = len(missing) == 0
    return {"passed": passed, "missing_fields": missing}


def task8_log_application(application: dict) -> str:
    return f"REF-{application['app_id']}"


def task9_verify_identity(application: dict) -> bool:
    return bool(application.get("id_document_valid"))


def task13_credit_check(application: dict) -> dict:
    score = mock_credit_bureau_api(application["pps_number"])
    return {"credit_score": score, "acceptable": score >= 600}


def task22_register_rtb(application: dict) -> str:
    return mock_rtb_portal_submit(application)


def task23_setup_utilities(application: dict) -> str:
    return mock_utility_provider_api(application)


def task26_archive(application: dict, result: dict, log_path: str):
    row = {
        "app_id": application["app_id"],
        "applicant_name": application["applicant_name"],
        "reference_no": result["reference_no"],
        "fields_valid": result["field_validation"]["passed"],
        "identity_verified": result["identity_verified"],
        "credit_score": result["credit_check"]["credit_score"],
        "credit_acceptable": result["credit_check"]["acceptable"],
        "rtb_registration_no": result.get("rtb_registration_no", ""),
        "utility_status": result.get("utility_status", ""),
        "status": result["status"],
        "processed_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_header = not _file_has_content(log_path)
    with open(log_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def _file_has_content(path: str) -> bool:
    try:
        with open(path, "r") as f:
            return bool(f.read().strip())
    except FileNotFoundError:
        return False


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_rpa_pipeline(application: dict, log_path: str = "rpa_case_log.csv") -> dict:
    result = {}

    viewing = task3_schedule_viewing(application["applicant_name"])
    result["viewing"] = viewing

    field_check = task7_validate_fields(application)
    result["field_validation"] = field_check

    if not field_check["passed"]:
        result["reference_no"] = None
        result["identity_verified"] = False
        result["credit_check"] = {"credit_score": None, "acceptable": False}
        result["status"] = "REJECTED - incomplete application"
        task26_archive(application, {
            "reference_no": "N/A", "field_validation": field_check,
            "identity_verified": False,
            "credit_check": {"credit_score": None, "acceptable": False},
            "status": result["status"],
        }, log_path)
        return result

    result["reference_no"] = task8_log_application(application)
    result["identity_verified"] = task9_verify_identity(application)
    result["credit_check"] = task13_credit_check(application)

    if result["identity_verified"] and result["credit_check"]["acceptable"]:
        result["status"] = "PASSED RPA STAGE - proceeding to AI agent review"
        result["rtb_registration_no"] = task22_register_rtb(application)
        result["utility_status"] = task23_setup_utilities(application)
    else:
        result["status"] = "FLAGGED - failed identity/credit check, needs manual review"

    task26_archive(application, result, log_path)
    return result


def main():
    with open("sample_data.json") as f:
        applications = json.load(f)

    log_path = "rpa_case_log.csv"
    open(log_path, "w").close()  # reset log for a clean demo run

    print("=" * 70)
    print("RPA AUTOMATION PIPELINE - Rental Property Application Process")
    print("=" * 70)

    for app in applications:
        print(f"\nProcessing {app['app_id']} ({app['applicant_name']})...")
        result = run_rpa_pipeline(app, log_path)
        for k, v in result.items():
            print(f"  {k}: {v}")

    print(f"\nAll cases archived to '{log_path}'.")


if __name__ == "__main__":
    main()
