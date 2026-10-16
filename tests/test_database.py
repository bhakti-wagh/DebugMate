"""Database unit tests use fake connections and never contact MySQL."""

import unittest
from unittest.mock import Mock, patch

import database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.connection = Mock()
        self.cursor = Mock()
        self.connection.cursor.return_value = self.cursor

    @patch("database.get_connection")
    def test_save_uses_placeholders_and_commits_all_result_fields(self, get_connection):
        get_connection.return_value = self.connection
        result = {
            "error_type": "CustomProblem", "explanation": "An unknown issue.",
            "suggested_fix": "Read the traceback.", "status": "unknown",
        }

        database.save_analysis("CustomProblem: hello", result)

        sql, values = self.cursor.execute.call_args.args
        self.assertIn("VALUES (%s, %s, %s, %s, %s)", sql)
        self.assertEqual(values, (
            "CustomProblem", "CustomProblem: hello", "An unknown issue.",
            "Read the traceback.", "unknown",
        ))
        self.connection.commit.assert_called_once()
        self.cursor.close.assert_called_once()
        self.connection.close.assert_called_once()

    @patch("database.get_connection")
    def test_recent_history_uses_bounded_parameterized_limit(self, get_connection):
        get_connection.return_value = self.connection
        self.cursor.fetchall.return_value = [{"error_type": "NameError"}]

        rows = database.get_recent_history(limit=5000)

        self.assertEqual(rows, [{"error_type": "NameError"}])
        sql, values = self.cursor.execute.call_args.args
        self.assertIn("LIMIT %s", sql)
        self.assertEqual(values, (200,))
        self.connection.cursor.assert_called_once_with(dictionary=True)

    @patch("database.get_connection")
    def test_dashboard_returns_total_and_grouped_counts(self, get_connection):
        get_connection.return_value = self.connection
        self.cursor.fetchone.return_value = {
            "total": 4, "distinct_error_types": 2, "recognized": 3, "uncertain": 1,
        }
        self.cursor.fetchall.side_effect = [
            [
                {"error_type": "NameError", "count": 3},
                {"error_type": "Unidentified", "count": 1},
            ],
            [{"error_type": "NameError", "status": "supported"}],
        ]

        stats = database.get_dashboard_stats()

        self.assertEqual(stats["total"], 4)
        self.assertEqual(stats["distinct_error_types"], 2)
        self.assertEqual(stats["recognized"], 3)
        self.assertEqual(stats["uncertain"], 1)
        self.assertEqual(stats["by_error_type"][0]["error_type"], "NameError")
        self.assertEqual(stats["recent_analyses"][0]["error_type"], "NameError")
        self.assertEqual(self.cursor.execute.call_count, 3)
        self.connection.close.assert_called_once()

    @patch("database.get_connection")
    def test_query_failure_becomes_database_error_and_closes_resources(self, get_connection):
        get_connection.return_value = self.connection
        self.cursor.execute.side_effect = RuntimeError("database detail")

        with self.assertRaises(database.DatabaseError):
            database.save_analysis("ValueError: bad", {"status": "supported"})

        self.cursor.close.assert_called_once()
        self.connection.close.assert_called_once()

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_environment_settings_fail_without_connecting(self):
        with self.assertRaises(database.DatabaseError) as raised:
            database.get_connection()
        self.assertIn("DB_HOST", raised.exception.safe_message)
        self.assertIn("DB_PASSWORD", raised.exception.safe_message)


if __name__ == "__main__":
    unittest.main()
