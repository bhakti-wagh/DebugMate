"""Route tests for the first DebugMate web milestone.

Install Flask from requirements.txt before running these tests. Keeping the
skip guard allows the diagnosis-only tests to run in a Python environment
where Flask has not been installed yet.
"""

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

    def test_home_page_has_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="error_text"', response.data)
        self.assertIn(b"Analyze Error", response.data)

    def test_post_shows_supported_diagnosis(self):
        response = self.client.post("/", data={"error_text": "NameError: name 'score' is not defined"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"NameError", response.data)
        self.assertIn(b"Likely causes", response.data)
        self.assertIn(b"Suggested next step", response.data)

    def test_post_empty_input_shows_helpful_message(self):
        response = self.client.post("/", data={"error_text": "  "})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please add an error message", response.data)

    def test_post_unknown_and_malformed_inputs_have_distinct_messages(self):
        unknown = self.client.post("/", data={"error_text": "The program behaved strangely"})
        malformed = self.client.post("/", data={"error_text": "Traceback (most recent call last):\n  File 'demo.py', line 1"})
        self.assertIn(b"No matching rule found", unknown.data)
        self.assertIn(b"Traceback looks incomplete", malformed.data)

    @patch("app.database.save_analysis")
    def test_post_saves_unknown_and_malformed_results(self, save_analysis):
        self.client.post("/", data={"error_text": "CustomProblem: example"})
        self.client.post("/", data={"error_text": "Traceback (most recent call last):\n  File 'demo.py', line 1"})
        self.assertEqual(save_analysis.call_count, 2)
        self.assertEqual(save_analysis.call_args_list[0].args[1]["status"], "unknown")
        self.assertEqual(save_analysis.call_args_list[1].args[1]["status"], "malformed")

    @patch("app.database.save_analysis")
    def test_post_empty_input_is_not_saved(self, save_analysis):
        self.client.post("/", data={"error_text": "  "})
        save_analysis.assert_not_called()

    @patch("app.database.save_analysis")
    def test_save_failure_shows_missing_setting_names_without_secret_values(self, save_analysis):
        save_analysis.side_effect = __import__("database").DatabaseError(
            "Missing required database environment settings.",
            safe_message="Missing settings: DB_HOST, DB_PASSWORD",
        )
        response = self.client.post("/", data={"error_text": "NameError: missing"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Diagnosis is ready", response.data)
        self.assertIn(b"DB_HOST, DB_PASSWORD", response.data)
        self.assertNotIn(b"actual-password", response.data)

    @patch("app.database.get_recent_history", return_value=[])
    def test_history_page_renders(self, get_history):
        response = self.client.get("/history")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No analyses have been saved yet", response.data)
        get_history.assert_called_once()

    @patch("app.database.get_dashboard_stats", return_value={
        "total": 3, "distinct_error_types": 1, "recognized": 2, "uncertain": 1,
        "by_error_type": [{"error_type": "NameError", "count": 2}],
        "recent_analyses": [{"error_type": "NameError", "status": "supported", "created_at": "today", "error_text": "NameError: missing"}],
    })
    def test_dashboard_shows_total_and_error_counts(self, get_stats):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b">3<", response.data)
        self.assertIn(b"NameError", response.data)
        self.assertIn(b"Distinct error types", response.data)
        self.assertIn(b"Recent analyses", response.data)
        get_stats.assert_called_once()

    @patch("app.database.get_recent_history", side_effect=__import__("database").DatabaseError("offline"))
    def test_history_database_failure_is_friendly(self, get_history):
        response = self.client.get("/history")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"History is temporarily unavailable", response.data)

    def test_submitted_html_is_escaped(self):
        response = self.client.post("/", data={"error_text": "<script>alert('x')</script>"})
        self.assertNotIn(b"<script>alert('x')</script>", response.data)


if __name__ == "__main__":
    unittest.main()
