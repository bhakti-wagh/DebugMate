"""Flask entry point for the DebugMate diagnosis page."""

from flask import Flask, render_template, request

from diagnosis import diagnose
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
            # The diagnosis engine reads this string as text; it never runs it.
            result = diagnose(error_text)
            # Empty submissions are validation feedback, not useful history.
            if result["status"] != "invalid":
                try:
                    database.save_analysis(error_text, result)
                except database.DatabaseError as exc:
                    # Keep the diagnosis available even if history storage is down.
                    database_message = (
                        "Diagnosis is ready, but DebugMate could not save it to history."
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
