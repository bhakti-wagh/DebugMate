# DebugMate Requirements

## Project overview

DebugMate is a beginner-friendly Python Error Diagnosis and Learning Assistant. A learner pastes a Python error message (and optionally the nearby code as plain text), and the application identifies supported error types, explains likely causes, and suggests a correction. The app also keeps a history of analyses so a learner can review earlier troubleshooting.

The first version uses clear, hand-written rules. It does not need a paid AI service. It never runs submitted code: it reads the text only. The project is being built as a learning exercise for an NSDC Python Programming certificate, so understandable code and documentation are important outcomes too.

## Objectives

- Help new Python learners understand common error messages rather than only showing a replacement.
- Give useful, cautious guidance for error types covered by the first version.
- Let a learner revisit past diagnoses.
- Demonstrate a small web application using Python, Flask, MySQL, HTML, CSS, Bootstrap, and `unittest`.
- Keep the initial implementation small enough to complete, explain, and demonstrate.

## Intended users

- **Primary user:** a beginner learning Python who can copy an error message into a form.
- **Project maintainer:** the student building and presenting the certificate project.

The first version assumes one learner using a local or classroom deployment. Accounts, multiple roles, and public hosting are outside the initial scope.

## Functional requirements

1. The home page must explain briefly what DebugMate does and provide a form for an error message. An optional code/context field may help the rules give a more relevant explanation.
2. The server must validate input, trim irrelevant outer whitespace, reject empty input, and enforce a documented maximum length.
3. The diagnosis engine must inspect text using a defined set of rules and return a structured result: detected/supported error type (when recognizable), likely cause, beginner-friendly explanation, suggested correction or next step, and whether the match is uncertain.
4. The first rule set should cover common beginner errors such as `SyntaxError`, `IndentationError`, `NameError`, `TypeError`, `ValueError`, `IndexError`, `KeyError`, `ZeroDivisionError`, and `AttributeError`. Rules should be easy to read and extend.
5. Unrecognized or incomplete input must receive a graceful response that says the error could not be confidently identified and offers general troubleshooting steps. It must not invent a certain answer.
6. The result page must show the original submitted message safely as text, alongside the diagnosis. User text must not be interpreted as HTML.
7. Each accepted diagnosis must be saved to MySQL with a timestamp, input text, optional context, detected type, explanation, suggestion, and confidence/unknown status. Database failure must produce a useful message and must not expose credentials or a raw stack trace.
8. A history page must show recent saved analyses in reverse chronological order. It should provide a useful empty state when there is no history.
9. The application must not execute, compile, import, or evaluate user-submitted code. The optional code/context field is stored/read as plain text only.
10. Database reads and writes must use parameterized queries. Database credentials and connection settings must come from environment variables, not source code.
11. Automated `unittest` coverage must check diagnosis rules, unknown input, validation, and database/query behavior using a testable boundary or test database.

## Non-functional requirements

- **Beginner readability:** use small modules, descriptive names, short functions, comments for non-obvious choices, and documented setup steps.
- **Safety:** never execute user content; escape it in HTML; use parameterized SQL; keep secrets out of Git and error messages.
- **Reliability:** empty, long, malformed, unsupported, and database-unavailable cases receive controlled responses.
- **Maintainability:** keep Flask routes, diagnosis rules, and database access in separate modules.
- **Usability:** pages work on desktop and mobile using Bootstrap, label every form field, and explain errors in plain language.
- **Performance:** for this single-user learning project, diagnosis should be immediate and history should be limited/paginated so it does not fetch an unbounded table.
- **Portability:** the app should run on a standard Python environment with Flask and a MySQL driver documented in setup instructions; no paid API is required.
- **Testability:** diagnosis logic should be callable without starting Flask or connecting to MySQL.

## Scope boundaries

The first version is rule-based, not a general Python interpreter or guaranteed debugging service. It does not run code, use an AI API, create accounts, or attempt to repair an entire program. Suggestions are educational hints and may not identify every root cause from an error message alone.

## Acceptance checks

- A learner can submit a supported error and see a type, explanation, and next-step suggestion.
- Unknown input gives an honest fallback instead of a crash or fabricated diagnosis.
- A diagnosis is saved and later visible on the history page when MySQL is available.
- Submitting code-like text never causes it to run.
- User text is rendered as text, database values use placeholders, and secrets are configured outside source files.
- Unit tests can run with Python's `unittest` framework.
