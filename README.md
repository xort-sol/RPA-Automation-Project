# Solution Implementation — Rental Property Application Process

Two automation solutions for the Irish Rental Property Application process,
implemented in Python.

## Files
- `sample_data.json` — 3 synthetic rental applications used by both scripts
- `rpa_automation.py` — RPA solution (Tasks 3, 7, 8, 9, 13, 22, 23, 26)
- `agentic_automation.py` — Agentic/AI solution (Tasks 12, 14, 15, 16, 17, 19, 20)
- `illustrative_agentic_output_example.md` — worked example of real model output
- `rpa_case_log.csv` — generated after running the RPA script
- `agentic_case_log.json` — generated after running the agentic script



## Running the RPA solution
```
python rpa_automation.py
```
Simulates: viewing scheduling, field validation, application logging,
identity verification, credit check, RTB registration, utility setup,
and archiving. External systems (credit bureau, RTB portal, utility
provider) are represented by mock functions, since live integrations
require commercial API credentials — this mirrors how a UiPath workflow
would be structured, with the mock functions standing in for the
Invoke Web Service / UI Automation activities.

## Running the agentic solution
```
export GEMINI_API_KEY="your-gemini-api-key"
python agentic_automation.py
```
Calls the Gemini API to interpret references, assess affordability,
flag inconsistencies, evaluate guarantors, compile a risk narrative,
generate a decision letter, and draft opening lease clauses. If
`GEMINI_API_KEY` is not set, the script falls back to a clearly-labelled
MOCK response so the pipeline can still be demonstrated end-to-end.

## Note on API keys
Per the assignment brief, any required API key must be included by you
when you submit/run the implementation. Do not commit real API keys to
any shared repository — set them as an environment variable at runtime.
