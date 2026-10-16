"""Unit tests for the rule-based diagnosis module."""

import unittest

from diagnosis import diagnose


class DiagnoseTests(unittest.TestCase):
    def test_supported_exception_names(self):
        names = [
            "NameError", "TypeError", "ValueError", "IndexError", "KeyError",
            "ZeroDivisionError", "AttributeError", "ImportError",
            "ModuleNotFoundError", "SyntaxError",
        ]
        for name in names:
            with self.subTest(name=name):
                result = diagnose("{}: example problem".format(name))
                self.assertEqual(result["status"], "supported")
                self.assertEqual(result["error_type"], name)
                self.assertTrue(result["explanation"])
                self.assertTrue(result["likely_causes"])
                self.assertTrue(result["suggested_fix"])

    def test_extracts_final_exception_from_traceback(self):
        traceback = """Traceback (most recent call last):
  File \"example.py\", line 4, in <module>
    print(missing_name)
NameError: name 'missing_name' is not defined"""
        result = diagnose(traceback)
        self.assertEqual(result["status"], "supported")
        self.assertEqual(result["error_type"], "NameError")
        self.assertEqual(result["message"], "name 'missing_name' is not defined")

    def test_module_not_found_is_not_misread_as_import_error(self):
        result = diagnose("ModuleNotFoundError: No module named 'sample'")
        self.assertEqual(result["error_type"], "ModuleNotFoundError")

    def test_unknown_exception_is_reported(self):
        result = diagnose("CustomProblem: something went wrong")
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["error_type"], "CustomProblem")

    def test_unrecognized_text_is_reported(self):
        result = diagnose("The program did something unexpected")
        self.assertEqual(result["status"], "unknown")
        self.assertIsNone(result["error_type"])

    def test_empty_and_non_text_inputs_are_invalid(self):
        for value in ("", "  \n", None, 123):
            with self.subTest(value=value):
                self.assertEqual(diagnose(value)["status"], "invalid")

    def test_incomplete_traceback_is_malformed(self):
        result = diagnose("Traceback (most recent call last):\n  File 'example.py', line 1")
        self.assertEqual(result["status"], "malformed")
        self.assertIsNone(result["error_type"])


if __name__ == "__main__":
    unittest.main()
