---
trigger: always_on
---

# Project Rules

## Data Usage

- Do not use mock data unless I explicitly ask for it.
- Do not fabricate API responses, database records, files, screenshots, logs, or test results.
- Use real project APIs, real database connections, real fixtures, or real user-provided data.
- If real data or credentials are unavailable, stop and explain what is missing instead of creating fake data.
- Clearly distinguish between real results and assumptions.

## Testing Requirements

- Any code change must be verified by actually running the relevant tests.
- Do not claim that tests passed unless they were actually executed.
- Always include the exact test command used.
- Always include a concise summary of the test result.
- If tests fail, report the failure honestly and explain the likely cause.

## Screenshot Requirements

- For UI changes, end-to-end tests, browser automation, visual verification, or any workflow involving a visible interface, screenshots must be captured and preserved.
- Screenshots should be saved in a persistent project folder such as:

```text
test-artifacts/screenshots/