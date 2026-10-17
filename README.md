# DebugMate

### Python Code Analysis and Learning Assistant

DebugMate is a beginner-friendly web application that checks pasted Python source code for a small set of statically detectable issues. It uses Python's built-in AST parser and readable rules to show issue counts, line numbers, explanations, and suggested next steps. When MySQL is configured, DebugMate also saves analysis history and displays dashboard metrics.

This is a student learning project. Its suggestions are educational hints, not guaranteed fixes. The project does not claim official NSDC approval or certification.

## What it does

- Parses Python source without executing, importing, or evaluating it.
- Detects syntax errors, common undefined names, likely use-before-assignment, literal division by zero, obvious literal type mismatches, known out-of-range sequence indexes, known missing literal dictionary keys, and a narrow factorial accumulator mistake.
- Shows issue totals, error and warning counts, source lines, beginner-friendly explanations, and suggested corrections.
- Handles empty and oversized submissions with clear status messages, and caps displayed findings at 100 plus a notice.
- Shows an analysis form, an Overview dashboard, and a searchable recent History page.
- Stores non-empty submissions and a compact analysis summary in MySQL. Detailed findings appear on the result page; the current history schema does not store a separate structured record for each finding. Empty submissions are not saved.
- Uses parameterized SQL and reads database settings from environment variables.
- Treats submitted content as text. It never runs, evaluates, compiles, or imports user-submitted code.
- Shows a useful message when the database is unavailable; analysis can still be displayed, but it cannot be saved at that time.

## Pages

| Page | URL | Purpose |
| --- | --- | --- |
| Overview | `/dashboard` | Database-backed totals, successfully analyzed and uncertain counts, an issue-category breakdown, and recent analyses. |
| Analyze Code | `/` | Accepts Python source through a POST form and displays static-analysis findings. |
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
|-- static_analyzer.py      # Safe AST-based code checks; does not execute source
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
|   `-- index.html          # Error form and analysis results
`-- tests/
    |-- test_app.py         # Flask route tests
    |-- test_database.py    # Database tests using mocks
    |-- test_diagnosis.py   # Original exception-message diagnosis tests
    `-- test_static_analyzer.py # Code analysis tests
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

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). Use the left navigation to open **Overview**, **Analyze Code**, or **History**.

The current entry point runs Flask with `debug=True`, intended only for local development. Do not expose this development server to the public Internet. If database settings are missing or MySQL is unreachable, the app displays a database notice. Diagnosis remains separate from database storage.

## Run the tests

From the project folder, run:

```powershell
python -m unittest discover -s tests -v
```

- `test_static_analyzer.py` covers findings, syntax errors, invalid/large input, and common false-positive cases.
- `test_diagnosis.py` continues to test the original standalone exception-message diagnosis module.
- `test_database.py` checks parameterized SQL calls, history limits, dashboard summaries, connection settings, and cleanup using mocks. It does not require a live MySQL server.
- `test_app.py` covers Flask routes, form behavior, and safe rendering. Flask must be installed for these tests to run; skipped route tests have not verified the web pages.

Review the command output for failures and skips. Mock-based tests do not prove that a live MySQL server, credentials, schema, and connector work together. The project has not been tested against your database unless you run it with your own configured MySQL instance.

## How diagnosis and storage work

1. The browser submits the form to Flask with POST.
2. Flask passes the submitted source text to `static_analyzer.analyze_code()`.
3. The analyzer parses the text into an AST and applies conservative checks; it never executes or imports the submission.
4. For non-empty input, Flask asks `database.save_analysis()` to store the source and a compact summary. SQL values are passed separately using MySQL Connector placeholders.
5. Overview and History request saved rows and counts from the database module. Jinja templates render dynamic text with HTML escaping enabled.

## Static-analysis limitations

Static analysis inspects source structure without running it. It cannot know every value or execution path, so DebugMate can miss real problems and some warnings may not apply on every path. Undefined-name checking is intentionally basic and can be incomplete around dynamic attributes, complex imports, closures, conditional assignments, and comprehension scopes. Type checking is limited to obvious literal mismatches. Index and dictionary checks only apply when their literal contents are known. Factorial detection uses a narrow naming-and-pattern rule. A clean result means only that the current rules found no issue; it does not prove the program is correct. Syntax errors stop the AST-based checks because Python cannot build a normal syntax tree from invalid source.
