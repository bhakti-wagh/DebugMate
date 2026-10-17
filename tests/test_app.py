"""Flask route tests, with database writes mocked where appropriate."""

import unittest
from unittest.mock import patch

try:
    import flask  # noqa: F401
except ImportError:
    flask = None


@unittest.skipIf(flask is None, "Flask is not installed; install requirements.txt to run route tests")
class FlaskRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app

        cls.app = create_app()
        cls.app.config.update(TESTING=True)

    def setUp(self):
        self.client = self.app.test_client()

    def test_home_page_has_code_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="error_text"', response.data)
        self.assertIn(b"Analyze Python code", response.data)
        self.assertIn(b"Analyze Code", response.data)
        self.assertIn(b"never executes or imports it", response.data)

    @patch("app.database.save_analysis")
    def test_post_shows_static_findings_and_saves_summary(self, save_analysis):
        response = self.client.post("/", data={"error_text": "def calculate():\n    print(result)\n    value = 10 / 0\n"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Total detected issues", response.data)
        self.assertIn(b"Undefined variable", response.data)
        self.assertIn(b"Division by zero", response.data)
        save_analysis.assert_called_once()
        self.assertEqual(save_analysis.call_args.args[1]["status"], "supported")
        self.assertIn("2 detected issues", save_analysis.call_args.args[1]["explanation"])

    def test_post_empty_input_shows_helpful_message(self):
        response = self.client.post("/", data={"error_text": "  "})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please add Python code", response.data)

    @patch("app.database.save_analysis")
    def test_post_syntax_error_explains_ast_checks_could_not_run(self, save_analysis):
        response = self.client.post("/", data={"error_text": "if True\n    pass\n"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Syntax error on line 1", response.data)
        self.assertIn(b"other static checks could not run", response.data)
        save_analysis.assert_called_once()
        self.assertEqual(save_analysis.call_args.args[1]["status"], "malformed")

    @patch("app.database.save_analysis")
    def test_database_failure_does_not_hide_analysis(self, save_analysis):
        import database

        save_analysis.side_effect = database.DatabaseError("offline")
        response = self.client.post("/", data={"error_text": "print(missing_name)"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Analysis is ready", response.data)
        self.assertIn(b"Undefined variable", response.data)

    @patch("app.database.save_analysis")
    def test_post_empty_input_is_not_saved(self, save_analysis):
        self.client.post("/", data={"error_text": "  "})
        save_analysis.assert_not_called()

    @patch("app.database.get_recent_history", return_value=[])
    def test_history_page_renders(self, get_history):
        response = self.client.get("/history")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No analyses have been saved yet", response.data)
        get_history.assert_called_once()

    @patch("app.database.get_dashboard_stats", return_value={
        "total": 3, "distinct_error_types": 1, "recognized": 2, "uncertain": 1,
        "by_error_type": [{"error_type": "Undefined variable", "count": 2}],
        "recent_analyses": [{"error_type": "Undefined variable", "status": "supported", "created_at": "today", "error_text": "print(missing)"}],
    })
    def test_dashboard_remains_available(self, get_stats):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b">3<", response.data)
        self.assertIn(b"Recent analyses", response.data)
        get_stats.assert_called_once()

    @patch("app.database.get_recent_history", side_effect=__import__("database").DatabaseError("offline"))
    def test_history_database_failure_is_friendly(self, get_history):
        response = self.client.get("/history")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"History is temporarily unavailable", response.data)

    def test_submitted_html_is_escaped(self):
        submitted = "print('<script>alert(1)</script>')"
        response = self.client.post("/", data={"error_text": submitted})
        self.assertNotIn(b"<script>alert(1)</script>", response.data)
        self.assertIn(b"&lt;script&gt;", response.data)


if __name__ == "__main__":
    unittest.main()
