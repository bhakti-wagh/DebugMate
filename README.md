# DebugMate — Python Error Diagnosis and Learning Assistant

DebugMate is a small learning web application for people who are beginning to use Python. A user pastes a Python exception line or traceback. Hand-written rules identify selected exception types and show a plain-language explanation, likely causes, and a next step. The application can save analyses to MySQL and show saved history and summary counts.

This is a student learning project. It does not guarantee that it can find the root cause of every error, and this repository does not imply official NSDC approval or certification.

## Features in the current code

- Rule-based diagnosis for `NameError`, `TypeError`, `ValueError`, `IndexError`, `KeyError`, `ZeroDivisionError`, `AttributeError`, `ImportError`, `ModuleNotFoundError`, and `SyntaxError`.
- Extraction of the last supported exception line from pasted traceback text.
- Separate responses for blank/non-text input, malformed tracebacks, unrecognized text, and unrecognized named exception types.
- A Flask form submitted with `POST` and HTML templates that auto-escape submitted text.
- No execution, evaluation, compilation, or import of submitted Python code.
- MySQL history storage through parameterized queries, with a recent-history page and dashboard totals.
- Friendly database-unavailable messages so diagnosis output can still be shown when saving fails.

The code saves non-empty outcomes including supported, unknown, and malformed diagnoses. It does not save invalid/empty input. The history query is capped at 50 by default; the database function allows a caller-supplied limit up to 200.

## Technologies

- Python
- Flask and Jinja templates
- HTML, CSS, Bootstrap 5.3.3 (loaded from a CDN by the browser)
- MySQL and `mysql-connector-python`
- Python standard-library `unittest` and `unittest.mock`

## Project structure

```text
DebugMate/
├── app.py                    # Flask application factory and web routes
├── database.py               # MySQL connection and history/statistics queries
├── diagnosis.py              # Standalone rule-based diagnosis function
├── requirements.txt          # Flask and MySQL Connector dependencies
├── schema.sql                # Creates debugmate_db and debug_history
├── .env.example              # Names of settings with placeholder values only
├── .gitignore                # Excludes .env, bytecode, and local virtual environments
├── docs/
│   ├── development_plan.md   # Earlier three-day development checklist
│   ├── project_report.md     # Certificate evaluation project report
│   ├── requirements.md       # Project objectives and requirements
│   ├── system_design.md      # Architecture notes
│   └── viva_questions.md    # Practice evaluation questions and answers
├── static/css/style.css      # Small project-specific styles
├── templates/
│   ├── dashboard.html        # Total analyses and counts by error type
│   ├── history.html          # Recent saved analyses
│   └── index.html            # Diagnosis form and result
└── tests/
    ├── test_app.py           # Flask route tests (require Flask)
    ├── test_database.py      # Mock-based database tests (no MySQL server)
    └── test_diagnosis.py     # Diagnosis rule tests
```

## Installation

Use a terminal opened in the project folder. Create and activate a virtual environment if desired, then install the declared dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The app and Flask route tests need Flask. Saving or reading history also needs a reachable MySQL server and `mysql-connector-python`. Do not install packages into a different Python environment than the one used to start DebugMate.

## MySQL configuration

The database module reads these process environment variables:

| Variable | Meaning | Example value |
| --- | --- | --- |
| `DB_HOST` | MySQL server address | `localhost` |
| `DB_PORT` | MySQL port (optional; defaults to `3306`) | `3306` |
| `DB_NAME` | Database name | `debugmate_db` |
| `DB_USER` | MySQL account name | Set your own account |
| `DB_PASSWORD` | Password for that account | Set privately in your environment |

`.env.example` is a reference containing placeholders; the application does **not** automatically read a `.env` file. Set variables in the shell or your operating system's environment settings. Example for PowerShell (replace the user and password locally; do not commit them):

```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_NAME = "debugmate_db"
$env:DB_USER = "your_mysql_username"
$env:DB_PASSWORD = "your_local_password"
```

The `.gitignore` excludes a file named `.env`, but secrets should still be handled carefully and never placed in Python source or `.env.example`.

## Database setup

Start your MySQL server and run the schema script once using a MySQL account that is allowed to create a database and table. For example, in PowerShell with the MySQL command-line client installed:

```powershell
mysql -u your_mysql_username -p < schema.sql
```

Enter the password when the client prompts. The script creates `debugmate_db` and the `debug_history` table. The table stores an ID, error type, submitted error text, explanation, suggested fix, status, and database-generated timestamp. The application does not create the database automatically.

Configure the application's `DB_USER` and `DB_PASSWORD` with credentials that can connect to and write to `debugmate_db`. For safer deployments, grant only the database permissions the application needs; the setup account that creates the schema can be separate.

## Start the application

With dependencies installed and environment variables set, run:

```powershell
python app.py
```

Open `http://127.0.0.1:5000/` in a browser. The other pages are `/history` and `/dashboard`. The current entry point enables Flask's development debug mode, so use it only on a local development machine; do not expose this development server to the public Internet.

If MySQL is unavailable, the app is designed to display a friendly database message. History and dashboard data will not be available until configuration and connectivity work.

## Tests

Run the full suite from the project folder:

```powershell
python -m unittest discover -s tests -v
```

`test_diagnosis.py` exercises the rule engine. `test_database.py` uses mocks and does not need a live MySQL server. `test_app.py` exercises Flask routes and does not need MySQL because its database calls are patched in route cases; it does require Flask to be installed. A skipped test is not a passing verification of that behavior. Check the command output for skips and failures.

## Current verification caveat

At the time the project report was prepared, the available Python environment did not have Flask installed. The most recent full test run discovered 22 tests: 12 passed, and 10 Flask route tests were skipped. The passing tests included all seven diagnosis tests and all five mocked database tests. No live MySQL server or installed connector was used to verify a database connection. See `docs/project_report.md` for the exact recorded result and limitations.
