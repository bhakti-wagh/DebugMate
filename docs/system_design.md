# DebugMate System Design

## Design at a glance

DebugMate is a small Flask web application with four cooperating parts:

1. **Frontend:** HTML templates, CSS, and Bootstrap show the form, diagnosis, and history.
2. **Flask backend:** receives browser requests, validates form input, calls the diagnosis engine, asks the database layer to save or load records, and chooses a page to return.
3. **Python diagnosis engine:** applies readable rules to error text and returns a result. It treats all input as text and never runs it.
4. **MySQL database:** stores each analysis and supplies recent records for history.

```text
Browser
  | GET/POST page request
  v
Flask routes -----> input validation
  |                     |
  |               Diagnosis engine (text rules only)
  |                     |
  +------> database access module ------> MySQL
  |
  +------> HTML template + Bootstrap/CSS ------> Browser response
```

The arrows describe data flow. The browser never connects directly to MySQL, and the diagnosis engine has no code execution feature.

## Request flow

### Submit an error

1. The browser sends the form contents to a Flask route using `POST`.
2. Flask checks that the message is present and within the size limit. Optional context is also plain text and size-limited.
3. Flask passes the strings to the diagnosis engine.
4. The engine checks for known error names and message patterns. It returns a structured result such as `error_type`, `cause`, `explanation`, `suggestion`, and `is_unknown`.
5. Flask passes the result and original text to the database module. That module inserts values with SQL placeholders, not by joining user text into a SQL string.
6. A result template displays the input and diagnosis. Template auto-escaping keeps submitted text from becoming executable HTML.

If no rule matches, the engine returns a clear “not recognized yet” explanation and general next steps. Unknown results can still be stored so history reflects what the learner tried.

### View history

1. The browser requests the history route with `GET`.
2. Flask asks the database module for a bounded page of recent rows, ordered newest first.
3. The template displays each row as escaped text. If there are no rows, it displays an empty-state message.

## Database design

The first version needs one table, for example `analyses`:

| Column | Suggested type | Purpose |
| --- | --- | --- |
| `id` | integer, primary key, auto increment | Identifies a saved analysis |
| `created_at` | timestamp/datetime | When the analysis was submitted |
| `error_text` | text | Error message supplied by the learner |
| `code_context` | text, nullable | Optional nearby code supplied as plain text |
| `error_type` | short varchar, nullable | Recognized error type; empty/NULL when unknown |
| `cause` | text | Likely cause explanation |
| `suggestion` | text | Suggested correction or next step |
| `is_unknown` | boolean | Indicates that no confident rule matched |

The database connection module reads values such as `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` from the process environment. A local `.env` file may be used during development only if it is excluded from version control. A `.env.example` may show variable names with harmless placeholders.

Every query uses the MySQL driver's parameter-placeholder syntax. For example, the `INSERT` statement contains placeholders and passes the submitted values separately. History uses a `LIMIT` and optional offset to keep results bounded. Table creation can be documented in a small SQL schema file rather than silently happening in every request.

## Suggested module boundaries

- **`app.py`:** creates/configures the Flask app and registers routes (or calls an app factory).
- **`routes.py`:** HTTP concerns only: form input, validation, calls to services, and responses.
- **`diagnosis.py`:** pure rule-based diagnosis functions; no Flask or database dependency.
- **`database.py`:** connection setup and parameterized insert/select functions.
- **`templates/`:** HTML pages; dynamic values are escaped by the template engine.
- **`static/`:** project CSS and optional small JavaScript enhancements.
- **`tests/`:** standard-library `unittest` cases for rules, validation, and database boundaries.

For a beginner project, these boundaries make it possible to test the diagnosis rules without launching a web server or needing MySQL.

## Safety and error handling

- Never call `eval`, `exec`, `compile`, `subprocess`, or dynamically import content from the form.
- Do not attempt to “test” a submitted program. Rule matching examines strings only.
- Set input length limits and HTML-escape values through normal template rendering.
- Use parameterized SQL for every value that comes from a request.
- Never put credentials in Python files or commit a real `.env` file.
- Catch expected database connection/query errors at the route or service boundary. Tell the learner that saving/history is temporarily unavailable; log useful technical detail without secrets or submitted sensitive data.
- Treat unknown patterns as unknown. The diagnosis is an educational hint, not a guarantee.

## Testing approach

Use Python `unittest` and keep the rules as plain functions. Example test groups:

- known error text returns the expected type and useful guidance;
- a message containing no supported pattern returns the unknown result;
- blank and too-long input is rejected before saving;
- database functions pass values separately from SQL text;
- Flask routes return the expected page/status for valid, invalid, and database-unavailable cases.

Database tests should use a test database or a mocked database boundary so the ordinary unit tests do not modify a learner's real history.
