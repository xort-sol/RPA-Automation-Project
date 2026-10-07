"""
Agentic / AI-Driven Automation
Irish Rental Property Application Process

Automates the JUDGEMENT-BASED, UNSTRUCTURED-REASONING tasks of the process:
  Task 12 - Contact previous landlord (interpret reference reply)
  Task 14 - Check income-to-rent affordability (holistic assessment)
  Task 15 - Flag document inconsistencies
  Task 16 - Guarantor processing (suitability evaluation)
  Task 17 - Compile applicant risk summary
  Task 19 - Generate personalized decision communication
  Task 20 - Draft tenancy lease agreement (clause selection)

This script calls the Google Gemini API to perform each reasoning step.
Set the GEMINI_API_KEY environment variable to run it against the real
model. If no key is present, the script automatically falls back to a
clearly-labelled MOCK response so the pipeline can still be demonstrated
end-to-end (useful for markers running the code without an API key).

Usage:
    export GEMINI_API_KEY="AQ...."
    python agentic_automation.py
"""

import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

USE_REAL_API = bool(os.environ.get("GEMINI_API_KEY"))

if USE_REAL_API:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    MODEL = "gemini-flash-latest"  # alias to Google's current flash model


def call_gemini(system: str, prompt: str, max_tokens: int = 400) -> str:
    """Wraps a single-turn Gemini API call. Falls back to a mock response
    if no API key is configured, so the pipeline still runs for demo/marking.
    Retries once on free-tier rate limits (429), honouring the server's
    requested retry delay."""
    if not USE_REAL_API:
        return f"[MOCK RESPONSE - set GEMINI_API_KEY to call the real model]\n" \
               f"(system: {system[:60]}...)"

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    max_output_tokens=max_tokens,
                ),
            )
            break
        except errors.ClientError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(20)
            else:
                raise
    return response.text


# ---------------------------------------------------------------------------
# Agentic workflow steps
# ---------------------------------------------------------------------------

def task12_interpret_reference(reply_text: str) -> str:
    system = ("You are a lettings assistant. Read a previous landlord's reference reply "
              "and summarise in 2 sentences whether it is positive, neutral, or negative, "
              "and note any red flags such as late payments or damage.")
    return call_gemini(system, reply_text)


def task14_assess_affordability(income: float, rent: float, bank_summary: str) -> str:
    system = ("You are a lettings affordability assessor. Given monthly income, monthly rent, "
              "and a bank statement summary, assess whether the applicant can comfortably "
              "afford the tenancy. Go beyond a simple income/rent ratio - consider income "
              "stability and spending patterns. Respond in 2-3 sentences with a clear verdict: "
              "Affordable / Borderline / Not Affordable.")
    prompt = f"Monthly income: EUR {income}\nMonthly rent: EUR {rent}\nBank statement summary: {bank_summary}"
    return call_gemini(system, prompt)


def task15_flag_inconsistencies(application: dict) -> str:
    system = ("You are a fraud/consistency reviewer for rental applications. Compare the "
              "employment letter, bank statement summary, and declared income for internal "
              "consistency. Flag any mismatches or unusual patterns in 2-3 sentences. If "
              "nothing is inconsistent, say so clearly.")
    prompt = (f"Declared monthly income: EUR {application['monthly_income']}\n"
              f"Employment letter: {application['employment_letter']}\n"
              f"Bank statement summary: {application['bank_statement_summary']}")
    return call_gemini(system, prompt)
task17_compile_risk_summary

def task16_evaluate_guarantor(guarantor_info: str) -> str:
    system = ("You are a lettings agent evaluating a guarantor's suitability for a tenancy. "
              "Assess their financial stability and suitability in 2 sentences.")
    return call_gemini(system, guarantor_info)


def task17_compile_risk_summary(applicant_name: str, reference_summary: str,
                                 affordability: str, inconsistencies: str,
                                 guarantor_eval: str = None) -> str:
    system = ("You are compiling a concise applicant risk narrative for a landlord, combining "
              "several assessment inputs into one coherent paragraph (4-5 sentences) with an "
              "overall recommendation: Low Risk / Medium Risk / High Risk.")
    prompt = (f"Applicant: {applicant_name}\n"
              f"Reference check: {reference_summary}\n"
              f"Affordability assessment: {affordability}\n"
              f"Consistency review: {inconsistencies}\n")
    if guarantor_eval:
        prompt += f"Guarantor evaluation: {guarantor_eval}\n"
    return call_gemini(system, prompt, max_tokens=500)


def task19_generate_decision_letter(applicant_name: str, decision: str, reason: str) -> str:
    system = ("You are a lettings agent writing a professional, empathetic decision letter "
              "to a rental applicant. Keep it under 120 words.")
    prompt = f"Applicant: {applicant_name}\nDecision: {decision}\nReason: {reason}"
    return call_gemini(system, prompt)


def task20_draft_lease_clause(applicant_name: str, monthly_rent: float, guarantor_required: bool) -> str:
    system = ("You are drafting the opening clauses of a standard Irish residential tenancy "
              "agreement. Include tenant name, rent amount, and a guarantor clause only if "
              "required. Keep it to 4-5 clauses, concise.")
    prompt = f"Tenant: {applicant_name}\nMonthly rent: EUR {monthly_rent}\nGuarantor required: {guarantor_required}"
    return call_gemini(system, prompt, max_tokens=500)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_agentic_pipeline(application: dict) -> dict:
    result = {}

    result["reference_review"] = task12_interpret_reference(application["previous_landlord_reply"])
    result["affordability"] = task14_assess_affordability(
        application["monthly_income"], application["monthly_rent"], application["bank_statement_summary"])
    result["inconsistencies"] = task15_flag_inconsistencies(application)

    guarantor_eval = None
    if application.get("guarantor_required"):
        guarantor_eval = task16_evaluate_guarantor(application["guarantor_info"])
        result["guarantor_evaluation"] = guarantor_eval

    result["risk_summary"] = task17_compile_risk_summary(
        application["applicant_name"], result["reference_review"],
        result["affordability"], result["inconsistencies"], guarantor_eval)

    # Simplified decision logic for demo purposes; in practice this stays with the human landlord/agent
    decision = "Approved"
    reason = "Application meets affordability and reference requirements."
    result["decision_letter"] = task19_generate_decision_letter(
        application["applicant_name"], decision, reason)

    result["lease_draft"] = task20_draft_lease_clause(
        application["applicant_name"], application["monthly_rent"], application.get("guarantor_required", False))

    return result


def main():
    with open("sample_data.json") as f:
        applications = json.load(f)

    print("=" * 70)
    print("AGENTIC/AI AUTOMATION PIPELINE - Rental Property Application Process")
    if not USE_REAL_API:
        print("(No GEMINI_API_KEY found - running in MOCK mode)")
    print("=" * 70)

    all_results = {}
    for app in applications:
        print(f"\nProcessing {app['app_id']} ({app['applicant_name']})...")
        result = run_agentic_pipeline(app)
        all_results[app["app_id"]] = result
        for k, v in result.items():
            print(f"\n  [{k}]\n  {v}")

    with open("agentic_case_log.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("\n\nAll agentic outputs saved to 'agentic_case_log.json'.")


if __name__ == "__main__":
    main()
