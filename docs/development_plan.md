# DebugMate Three-Day Development Plan

This plan aims for a small, presentable first version. Each day ends with something understandable and reviewable. The plan does not require a paid AI API or running submitted code.

## Day 1 — Define and build the diagnosis core

- [ ] Review the requirements and system design; agree on the first supported error types.
- [ ] Create the planned project folders and a minimal Flask application entry point.
- [ ] Implement input limits and a rule-based diagnosis function in a separate module.
- [ ] Return a structured result for supported errors and an honest fallback for unknown input.
- [ ] Add `unittest` cases for each initial rule, unknown text, empty input, and size limits.
- [ ] Explain the diagnosis flow in the project README in beginner-friendly steps.

**Day 1 result:** diagnosis works as a plain Python function and its rules have unit tests, without MySQL being required to understand them.

## Day 2 — Add pages and persistent history

- [ ] Build a Bootstrap form page and a result page using Flask templates.
- [ ] Keep submitted error/context values as plain text; rely on template escaping.
- [ ] Add environment-based MySQL connection settings and a documented schema.
- [ ] Implement database insert and recent-history queries using parameter placeholders.
- [ ] Add a history page, including the no-records state and a bounded result count.
- [ ] Handle database unavailable errors without showing secrets or raw tracebacks.
- [ ] Add tests for route validation and database calls (using a test boundary/mock where suitable).

**Day 2 result:** learner can submit a message, see a diagnosis, and—when MySQL is configured—review saved history.

## Day 3 — Verify, polish, and prepare the demonstration

- [ ] Run the full `unittest` suite and fix failures.
- [ ] Manually walk through supported, unknown, empty, and too-long inputs.
- [ ] Confirm submitted code is never executed and check templates display input safely.
- [ ] Review every SQL statement for parameterization and check no credential is committed.
- [ ] Improve labels, error messages, spacing, and mobile layout with Bootstrap/CSS.
- [ ] Finish setup instructions, environment-variable example, schema instructions, and known limitations.
- [ ] Prepare a short certificate-project demo: submit a common error, explain the rule/result, and open history.

**Day 3 result:** a small tested demonstration with clear setup instructions and known limitations.

## Suggested first release boundary

Start with the common error types listed in `requirements.md`. Avoid adding accounts, deployment automation, arbitrary code execution, or external AI until the simple flow is working and understood. If time is short, preserve the tested diagnosis and unknown fallback first, then complete history and visual polish.
