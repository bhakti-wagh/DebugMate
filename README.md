# DebugMate

### Python Error Diagnosis and Learning Assistant

DebugMate is a beginner-friendly web application for understanding common Python errors. Paste an exception message or traceback to see a rule-based explanation, likely causes, and a suggested next step. When MySQL is configured, DebugMate also saves analysis history and displays a dashboard.

This is a student learning project. Its suggestions are educational hints, not guaranteed fixes. The project does not claim official NSDC approval or certification.

## What it does

- Recognizes `NameError`, `TypeError`, `ValueError`, `IndexError`, `KeyError`, `ZeroDivisionError`, `AttributeError`, `ImportError`, `ModuleNotFoundError`, and `SyntaxError`.
- Extracts a supported exception name and message from pasted traceback text when possible.
- Gives separate responses for empty input, malformed tracebacks, and errors without a matching rule.
- Shows an analysis form, an Overview dashboard, and a searchable recent History page.
- Stores non-empty diagnoses in MySQL, including unknown and malformed results. Empty or invalid submissions are not saved.
- Uses parameterized SQL and reads database settings from environment variables.
- Treats submitted content as text. It never runs, evaluates, compiles, or imports user-submitted code.
- Shows a useful message when the database is unavailable; diagnosis can still be displayed, but it cannot be saved at that time.

## Pages

| Page | URL | Purpose |
| --- | --- | --- |
| Overview | `/dashboard` | Database-backed totals, recognized and uncertain counts, an error-type breakdown, and recent analyses. |
| Analyze Error | `/` | Accepts an error message or traceback through a POST form and displays the diagnosis. |
| History | `/history` | Shows up to 50 recent analyses, with client-side search and expandable details. |

## Built with

- Python and Flask
- MySQL and `mysql-connector-python`
- HTML, CSS, Bootstrap 5 (stylesheet loaded from a CDN)
- Jinja templates
- Python's built-in `unittest` and `unittest.mock`

## Project layout

```text
DebugMate/
|-- app.py                  # Flask application factory and routes
|-- diagnosis.py            # Standalone rule-based diagnosis engine
|-- database.py             # Environment-based MySQL connection and queries
|-- requirements.txt        # Python package requirements
|-- schema.sql              # Creates debugmate_db and debug_history
|-- .env.example            # Environment variable names with placeholder values
|-- .gitignore              # Ignores local secrets, bytecode, and virtual environments
|-- docs/
|   |-- development_plan.md
|   |-- project_report.md
|   |-- requirements.md
|   |-- system_design.md
|   `-- viva_questions.md
|-- static/
|   |-- css/style.css       # Responsive application styles
|   `-- js/history.js       # Client-side filtering of the recent history list
|-- templates/
|   |-- base.html           # Shared navigation and page layout
|   |-- dashboard.html      # Overview dashboard
|   |-- history.html        # Recent analysis history
|   `-- index.html          # Error form and diagnosis results
`-- tests/
    |-- test_app.py         # Flask route tests
    |-- test_database.py    # Database tests using mocks
    `-- test_diagnosis.py   # Diagnosis engine tests
```

## Set up the project

Open PowerShell in the project folder. Create and activate a virtual environment, then install the listed packages:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, you can run its Python directly:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Use the same Python environment to run the application and tests. The project does not install packages automatically.

## Configure MySQL

Start a MySQL server. The database module reads these environment variables:

| Variable | Required? | Description | Typical local value |
| --- | --- | --- | --- |
| `DB_HOST` | Yes | MySQL server host | `localhost` |
| `DB_PORT` | No | MySQL server port; defaults to `3306` | `3306` |
| `DB_NAME` | Yes | Database name | `debugmate_db` |
| `DB_USER` | Yes | MySQL username | Your local MySQL account |
| `DB_PASSWORD` | Yes | Password for that account | Set privately in your environment |

`.env.example` documents the variable names, but the application does not automatically load a `.env` file. Set the values in the shell before starting the app. For example:

```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_NAME = "debugmate_db"
$env:DB_USER = "your_mysql_username"
$env:DB_PASSWORD = "your_local_password"
```

Replace the example username and password with your own values. Do not put real credentials in source code, `.env.example`, screenshots, or Git commits. A real `.env` file is excluded by `.gitignore`, but it is not read by the current application.

## Create the database and table

Run `schema.sql` once with a MySQL account permitted to create databases and tables. The script creates database `debugmate_db` and table `debug_history`. The table stores an auto-increment ID, error type, submitted error text, explanation, suggested fix, diagnosis status, and a timestamp generated by MySQL. The Flask app does not create the schema automatically.

One way to run the script with the MySQL command-line client is:

```powershell
mysql -u your_mysql_username -p
```

After entering the password at the prompt, run the schema file from the MySQL prompt (replace the path if your project is elsewhere):

```sql
SOURCE C:/Users/Bhakti/Documents/GitHub/DebugMate/schema.sql;
```

Then exit MySQL with `exit`. Configure `DB_USER` and `DB_PASSWORD` with an account that can connect to `debugmate_db` and read/write its history table. The setup account may be different from the application account.

## Run DebugMate

With dependencies installed, MySQL running, the schema created, and environment variables set:

```powershell
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). Use the left navigation to open **Overview**, **Analyze Error**, or **History**.

The current entry point runs Flask with `debug=True`, intended only for local development. Do not expose this development server to the public Internet. If database settings are missing or MySQL is unreachable, the app displays a database notice. Diagnosis remains separate from database storage.

## Run the tests

From the project folder, run:

```powershell
python -m unittest discover -s tests -v
```

- `test_diagnosis.py` covers supported exceptions, traceback extraction, unknown errors, empty input, and malformed tracebacks.
- `test_database.py` checks parameterized SQL calls, history limits, dashboard summaries, connection settings, and cleanup using mocks. It does not require a live MySQL server.
- `test_app.py` covers Flask routes, form behavior, and safe rendering. Flask must be installed for these tests to run; skipped route tests have not verified the web pages.

Review the command output for failures and skips. Mock-based tests do not prove that a live MySQL server, credentials, schema, and connector work together. The project has not been tested against your database unless you run it with your own configured MySQL instance.

## How diagnosis and storage work

1. The browser submits the form to Flask with POST.
2. Flask passes the submitted text to `diagnosis.diagnose()`.
3. The diagnosis engine returns a status, detected type (when available), explanation, likely causes, and suggested fix. It inspects text only.
4. For non-empty input, Flask asks `database.save_analysis()` to store the result. SQL values are passed separately using MySQL Connector placeholders.
5. Overview and History request saved rows and counts from the database module. Jinja templates render dynamic text with HTML escaping enabled.

The engine supports a defined set of patterns. It may not identify the root cause if an error message is incomplete or unusual, so treat its output as a learning aid and check the traceback and course materials.
