# DebugMate — Python Error Diagnosis and Learning Assistant

## Abstract

DebugMate is a beginner-focused web application designed to help learners understand common Python exceptions. A user submits an error message or traceback through a Flask form. A separate Python module uses text-based rules to identify selected exception types and returns an explanation, likely causes, and a practical next step. A database module is designed to save analysis history in MySQL using parameterized queries. Flask pages present recent history and summary counts. Submitted text is not executed. The diagnosis and mocked database unit tests passed in the recorded test run; Flask route tests were skipped because Flask was unavailable, and no live MySQL connection was tested.

## Problem statement

New programmers often see a traceback without knowing which part is important, why the error happened, or what to inspect next. DebugMate aims to turn selected exception messages into understandable hints, while keeping the first implementation small enough for a student to study and explain.

## Objectives

- Recognize a defined set of common Python exception names from pasted text.
- Explain common causes in beginner-friendly language.
- Suggest a useful next step without claiming certainty about the program's full context.
- Give an honest fallback for unknown or incomplete input.
- Present the diagnosis in a small Flask web interface.
- Provide code paths to save and review analysis history and see aggregate counts.
- Use parameterized SQL and environment-based database credentials.
- Keep diagnosis rules independent of Flask and MySQL.
- Verify logic with `unittest`, using mocks for database operations.

## Scope

### Included in the current source

- A rule-based diagnosis engine for `NameError`, `TypeError`, `ValueError`, `IndexError`, `KeyError`, `ZeroDivisionError`, `AttributeError`, `ImportError`, `ModuleNotFoundError`, and `SyntaxError`.
- Extraction of a supported exception and message from the last matching line of traceback text.
- Distinct result statuses: `supported`, `unknown`, `invalid`, and `malformed`.
- A Flask home route supporting GET and POST, plus history and dashboard GET routes.
- MySQL connection, insert, recent-history, and dashboard-count functions.
- A schema script for `debugmate_db` and `debug_history`.
- Unit tests for diagnosis behavior and mocked database behavior; Flask route tests are present but depend on Flask.

### Excluded

- Executing, compiling, or evaluating submitted code.
- Paid AI service integration, user accounts, multi-user authorization, or production deployment.
- A guarantee that the suggested cause is the only or correct cause for a complete program.
- Automatic database/schema creation by the Flask app. An operator must run `schema.sql`.

## Requirements

### Functional requirements

1. Accept error text through an HTML form submitted with POST.
2. Diagnose the submitted text without executing it.
3. Return type, explanation, likely causes, and suggested fix for supported errors.
4. Distinguish blank input, unknown text/named exceptions, and incomplete tracebacks.
5. Save non-empty diagnosis outcomes to history, including unknown and malformed outcomes; skip invalid empty input.
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
Diagnosis engine (diagnosis.py)    Database layer (database.py)
  | structured result                | parameterized SQL
  +---------------------> MySQL debugmate_db
  |
  v
Jinja templates + Bootstrap/CSS -> Browser
```

The diagnosis module does not import Flask or the database layer. The home route calls `diagnose()` and then passes the text and result to `database.save_analysis()` except for invalid input. The database module owns connection and SQL details. Templates display dynamic text through Jinja, whose normal auto-escaping is enabled. The history route requests recent rows; the dashboard route requests the total and per-type counts.

## Database design

`schema.sql` creates database `debugmate_db` using UTF-8 (`utf8mb4`) and table `debug_history` using InnoDB.

| Column | Type | Meaning |
| --- | --- | --- |
| `id` | `BIGINT UNSIGNED`, auto-increment primary key | Unique history row |
| `error_type` | nullable `VARCHAR(100)` | Detected type, or NULL if none was identified |
| `error_text` | `MEDIUMTEXT` | User-submitted error or traceback text |
| `explanation` | `TEXT` | Diagnosis explanation |
| `suggested_fix` | `TEXT` | Suggested next step |
| `status` | `VARCHAR(20)` | `supported`, `unknown`, or `malformed` for persisted submissions |
| `created_at` | timestamp, defaults to current time | Analysis time |

Indexes are defined for timestamp and error type. The insert uses five `%s` placeholders and supplies values as a separate tuple. The history query parameterizes its `LIMIT`. Dashboard SQL aggregates rows. Database credentials are read from `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`; port defaults to 3306. `.env.example` contains placeholder values only. The code does not load `.env` automatically.

## Implementation details

- **`diagnosis.py`:** contains the known-type guidance dictionary, exception-line patterns, and `diagnose(error_text)`. It returns a dictionary with `status`, `error_type`, `message`, `explanation`, `likely_causes`, and `suggested_fix`. It inspects strings only.
- **`app.py`:** defines `create_app()` and routes `/`, `/history`, and `/dashboard`. Database errors are caught and translated to friendly page messages. The local entry point runs Flask with development debug mode enabled.
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
| Diagnosis (`test_diagnosis.py`) | Supported exception names, traceback extraction, ModuleNotFoundError ordering, custom unknown exception, plain unrecognized text, invalid input, incomplete traceback | 7 passed |
| Database (`test_database.py`) | Parameterized insert values and commit, bounded history limit, dashboard aggregation, query failure cleanup, missing environment variables | 5 passed using mocks; no live MySQL server used |
| Flask routes (`test_app.py`) | Home form, supported diagnosis display, empty/unknown/malformed messages, save behavior, history/dashboard pages, safe HTML rendering, DB failure message | 10 skipped because Flask is not installed in the available Python environment |

Exact test summary:

```text
Ran 22 tests in 0.009s
OK (skipped=10)
```

Python syntax compilation also passed for the application, diagnosis/database modules, and test modules. The skipped route tests are not counted as verified behavior. No live database connection or browser demonstration was performed, so end-to-end persistence and page rendering remain to be verified in an environment with the dependencies and MySQL configured.

## Limitations

- Rule matching supports only the exception types listed above; `IndentationError` is not a dedicated rule in the current engine.
- Text-only rules cannot inspect variables, program state, or source code context and may not identify the true cause.
- Ordinary text may be unrecognized; the unknown response should be treated as guidance, not a definitive diagnosis.
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
- Add more diagnosis rules, including `IndentationError`, with tests for each new pattern.
- Add account support only if the project needs separate learner histories.
- Bundle Bootstrap locally for offline demonstrations and add accessibility review.
- Turn off debug mode by default outside a local development run.

## Screenshot and demonstration plan

Capture the home/form, one supported diagnosis, one unknown or malformed case, the history page, and the dashboard. Before the evaluation, run Flask with dependencies installed and MySQL configured; otherwise clearly demonstrate only the parts that are available. Never show database passwords or private submitted text in screenshots. A short walkthrough can explain form POST, pure text-based diagnosis, parameterized insert, and the two database-backed pages.
