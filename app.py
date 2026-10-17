"""Flask entry point for the DebugMate static code analyzer."""

from flask import Flask, render_template, request

from static_analyzer import analyze_code
import database


def create_app():
    """Create the Flask application (a small app factory helps route testing)."""
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def home():
        error_text = ""
        result = None
        database_message = None

        if request.method == "POST":
            error_text = request.form.get("error_text", "")
            # The analyzer parses source into an AST; it never runs it.
            result = analyze_code(error_text)
            # Empty submissions are validation feedback, not useful history.
            if result["status"] != "invalid":
                try:
                    # The existing schema stores one summary row. Map richer
                    # analyzer states to the two existing dashboard groups.
                    saved_result = dict(result)
                    saved_result["status"] = result["history_status"]
                    database.save_analysis(error_text, saved_result)
                except database.DatabaseError as exc:
                    # Keep the diagnosis available even if history storage is down.
                    database_message = (
                        "Analysis is ready, but DebugMate could not save it to history."
                        + _safe_database_detail(exc)
                        + " Check the database settings and try again later."
                    )

        return render_template(
            "index.html", error_text=error_text, result=result,
            database_message=database_message, active_page="analyze",
        )

    @app.route("/history")
    def history():
        try:
            analyses = database.get_recent_history()
            database_message = None
        except database.DatabaseError as exc:
            analyses = []
            database_message = (
                "History is temporarily unavailable."
                + _safe_database_detail(exc)
                + " Check the database settings and try again later."
            )
        return render_template(
            "history.html", analyses=analyses,
            database_message=database_message, active_page="history",
        )

    @app.route("/dashboard")
    def dashboard():
        try:
            stats = database.get_dashboard_stats()
            database_message = None
        except database.DatabaseError as exc:
            stats = None
            database_message = (
                "Dashboard data is temporarily unavailable."
                + _safe_database_detail(exc)
                + " Check the database settings and try again later."
            )
        return render_template(
            "dashboard.html", stats=stats,
            database_message=database_message, active_page="overview",
        )

    return app


def _safe_database_detail(error):
    """Return only explicitly approved diagnostic text, never driver details."""
    detail = getattr(error, "safe_message", None)
    return " " + detail + "." if detail else ""


if __name__ == "__main__":
    create_app().run(debug=True)
