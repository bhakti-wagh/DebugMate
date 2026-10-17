# DebugMate — Python Code Analysis and Learning Assistant

## Abstract

DebugMate is a beginner-focused web application that examines pasted Python source using the standard-library AST parser. A separate static-analysis module reports a limited set of syntax and likely code issues with source locations, explanations, and suggested next steps. Submitted code is never executed or imported. Flask presents the findings; the existing MySQL schema stores a compact submission summary and powers history and dashboard metrics. In the recorded run, 26 tests passed and 10 Flask route tests were skipped because Flask was unavailable; no live MySQL connection or browser test was performed.

## Problem statement

New programmers may have code that is wrong before they have a traceback, and may not know where to look. DebugMate aims to point out a few issues that can be found safely from source structure and explain them in simple language, while keeping the implementation small enough for a student to study.

## Objectives

- Accept Python source and inspect its syntax tree without executing it.
- Detect a limited set of statically visible issues and explain them in beginner-friendly language.
- Show issue counts, severity, line and column where known, code excerpts, and suggested next steps.
- Report syntax and size-limit failures clearly; a clean scan must not be presented as proof of correctness.
- Present analysis in the existing Flask interface.
- Provide code paths to save and review analysis history and see aggregate counts.
- Use parameterized SQL and environment-based database credentials.
- Keep static analysis independent of Flask and MySQL.
- Verify logic with `unittest`, using mocks for database operations.

## Scope

### Included in the current source

- The original exception-message module remains independently available and tested, but the web form uses `static_analyzer.py`.
- AST checks for syntax errors, common undefined names and use-before-assignment, literal division by zero and obvious literal type mismatches, known literal sequence/dictionary lookups, and a narrow factorial initialization pattern.
- Web-analysis statuses include `analyzed`, `syntax_error`, `invalid`, and `analysis_failed`.
- A Flask home route supporting GET and POST, plus history and dashboard GET routes.
- MySQL connection, insert, recent-history, and dashboard-count functions.
- A schema script for `debugmate_db` and `debug_history`.
- Unit tests for static analysis, the retained diagnosis module, and mocked database behavior; Flask route tests are present but depend on Flask.

### Excluded

- Executing, compiling, or evaluating submitted code.
- Paid AI service integration, user accounts, multi-user authorization, or production deployment.
- A guarantee that the suggested cause is the only or correct cause for a complete program.
- Automatic database/schema creation by the Flask app. An operator must run `schema.sql`.

## Requirements

### Functional requirements

1. Accept Python source through an HTML form submitted with POST.
2. Analyze source structure without executing or importing it.
3. Return issue category, severity, source location where known, explanation, and suggested fix.
4. Distinguish blank input, syntax failures, analysis limits, and successful scans with or without findings.
5. Save non-empty analysis summaries to history; skip invalid empty input.
6. Show recent saved analyses at `/history`.
7. Show total analyses and grouped counts by error type at `/dashboard`.
8. Use environment variables for database connection settings and parameter placeholders for database values.

### Non-functional requirements

- Keep diagnosis independent from web and persistence code.
- Keep code and explanations understandable to beginners.
- Render submitted content as escaped text.
- Keep credentials out of tracked configuration examples.
- Fail gracefully when the database cannot be reached.
- Use bounded recent-history results and standard-library unit tests.

## System architecture

```text
Browser
  | GET / or POST /
  v
Flask application (app.py)
  | POST text string                 | history/dashboard requests
  v                                  v
AST static analyzer               Database layer (database.py)
  | structured findings              | parameterized SQL
  +---------------------> MySQL debugmate_db
  |
  v
Jinja templates + Bootstrap/CSS -> Browser
```

`static_analyzer.py` does not import Flask or the database layer. The home route calls `analyze_code()` and passes its result to `database.save_analysis()` except for empty input. The database module owns connection and SQL details. The existing schema stores one compact summary per submission rather than a normalized row per finding. Templates display dynamic text through Jinja auto-escaping. The history route requests recent rows; the dashboard route requests totals and grouped categories.

## Database design

`schema.sql` creates database `debugmate_db` using UTF-8 (`utf8mb4`) and table `debug_history` using InnoDB.

| Column | Type | Meaning |
| --- | --- | --- |
| `id` | `BIGINT UNSIGNED`, auto-increment primary key | Unique history row |
| `error_type` | nullable `VARCHAR(100)` | First issue category or `StaticAnalysis` for a clean scan |
| `error_text` | `MEDIUMTEXT` | User-submitted Python source text |
| `explanation` | `TEXT` | Compact issue-count summary |
| `suggested_fix` | `TEXT` | Suggested next steps joined as readable text |
| `status` | `VARCHAR(20)` | `supported` for parsed scans; `malformed` for syntax/parser failures |
| `created_at` | timestamp, defaults to current time | Analysis time |

Indexes are defined for timestamp and error type. The insert uses five `%s` placeholders and supplies values as a separate tuple. The history query parameterizes its `LIMIT`. Dashboard SQL aggregates rows. Database credentials are read from `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`; port defaults to 3306. `.env.example` contains placeholder values only. The code does not load `.env` automatically.

## Implementation details

- **`static_analyzer.py`:** contains `analyze_code(source)`, which parses source with `ast.parse()` and runs conservative visitor rules. It returns structured issue details and does not execute code.
- **`diagnosis.py`:** retains the original standalone exception-message rules and tests; the current web form no longer uses it.
- **`app.py`:** defines `create_app()` and routes `/`, `/history`, and `/dashboard`. The home route runs static analysis and stores a compact summary. Database errors are caught and translated to friendly page messages.
- **`database.py`:** validates required environment settings, imports the MySQL connector when a connection is requested, executes parameterized statements, commits inserts, and closes cursors/connections. It raises `DatabaseError` with messages that do not include connection credentials.
- **Templates and CSS:** `index.html` is the form/result page; `history.html` presents saved rows; `dashboard.html` presents aggregate counts. Bootstrap is loaded from a public CDN, with additional CSS in `static/css/style.css`.
- **Configuration:** `requirements.txt` declares Flask and MySQL Connector. `.gitignore` excludes `.env`, bytecode caches, and common virtual environment directories.

## Test cases and recorded results

The full command used from the project root was:

```text
python -m unittest discover -s tests -v
```

The shell did not expose `python` by that command name, so the same unittest invocation was run with the available bundled Python executable, from the project root.

| Test group | Checks | Recorded result |
| --- | --- | --- |
| Original diagnosis (`test_diagnosis.py`) | Exception names and traceback handling, unknown and invalid inputs | 7 passed |
| Static analyzer (`test_static_analyzer.py`) | Syntax, names, use before assignment, literal operations/lookups, factorial pattern, false-positive checks, size and finding limits | 14 passed |
| Database (`test_database.py`) | Parameterized insert, bounded history, dashboard aggregation, cleanup, missing settings | 5 passed using mocks; no live MySQL server used |
| Flask routes (`test_app.py`) | Code form/results, syntax and empty input, saves, history/dashboard, escaping, DB failure | 10 skipped because Flask is not installed in the available Python environment |

Exact test summary:

```text
Ran 36 tests in 0.029s
OK (skipped=10)
```

Python syntax compilation also passed for the application, diagnosis/database modules, and test modules. The skipped route tests are not counted as verified behavior. No live database connection or browser demonstration was performed, so end-to-end persistence and page rendering remain to be verified in an environment with the dependencies and MySQL configured.

## Limitations

- Static rules cover only a subset of Python and cannot know all runtime values, control-flow paths, or dynamic behavior.
- Undefined-name checking is intentionally basic; dynamic attributes, complex imports, conditional assignments, closures, and comprehension scopes are incomplete.
- Type mismatch checks are limited to obvious literal cases; list and dictionary checks need uniquely known literal contents.
- The factorial check is a narrow naming-and-pattern heuristic, not a general logical-error detector.
- A no-issues result means no current rule matched, not that the program is correct.
- History stores a compact per-submission summary; structured findings are not stored separately in the existing schema.
- Flask route tests were skipped in the available environment because Flask was missing.
- Database tests use mocks; they do not prove the installed connector, credentials, MySQL schema, or server configuration works together.
- `schema.sql` must be run manually. The app does not create the database or table.
- `.env.example` is not automatically loaded; environment variables must be set in the shell or operating system.
- Bootstrap depends on a CDN, so styling may not load without network access.
- The entry point enables Flask debug mode and is intended for local development only.
- There is no user authentication or separation of different learners' histories.

## Future enhancements

- Install dependencies in a dedicated environment and run all Flask route tests.
- Test setup, inserts, and reads against a local disposable MySQL database.
- Add an explicit configuration loader only if a dotenv dependency is intentionally selected; otherwise keep shell environment configuration.
- Add input-size limits, pagination controls, and an optional delete/export feature with clear privacy behavior.
- Add more static-analysis rules, including a reliable `IndentationError` display and additional tested code patterns.
- Add account support only if the project needs separate learner histories.
- Bundle Bootstrap locally for offline demonstrations and add accessibility review.
- Turn off debug mode by default outside a local development run.

## Screenshot and demonstration plan

Capture the Analyze Code form, one sample with findings, one syntax-error case, the history page, and the dashboard. Before the evaluation, run Flask with dependencies installed and MySQL configured; otherwise clearly demonstrate only the parts that are available. Never show database passwords or private submitted code in screenshots. A short walkthrough can explain the POST form, AST-based static checks, parameterized insert, and the database-backed pages.
