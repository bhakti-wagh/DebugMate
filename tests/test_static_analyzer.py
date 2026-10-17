"""Tests for conservative code inspection that never runs submitted source."""

import unittest

from static_analyzer import MAX_ISSUES, MAX_SOURCE_LENGTH, analyze_code


class StaticAnalyzerTests(unittest.TestCase):
    def test_valid_code_has_no_findings(self):
        result = analyze_code("""message = 'hello'
def greet(name):
    return message + name
for item in [1, 2]:
    print(item)
class Box:
    label = 'box'
""")
        self.assertEqual(result["status"], "analyzed")
        self.assertEqual(result["issue_count"], 0)
        self.assertEqual(result["summary"], "No issues detected")

    def test_undefined_name_has_line_and_fix(self):
        result = analyze_code("def calculate():\n    print(result)\n")
        issue = result["issues"][0]
        self.assertEqual(issue["category"], "Undefined variable")
        self.assertEqual(issue["line"], 2)
        self.assertIn("Define `result`", issue["suggested_fix"])

    def test_use_before_assignment_is_detected(self):
        result = analyze_code("def sample():\n    print(value)\n    value = 3\n")
        self.assertTrue(any(item["category"] == "Use before assignment" for item in result["issues"]))

    def test_module_name_used_before_assignment_is_detected(self):
        result = analyze_code("print(score)\nscore = 10\n")
        issue = result["issues"][0]
        self.assertEqual(issue["category"], "Use before assignment")
        self.assertEqual(issue["line"], 1)

    def test_syntax_error_has_message_line_column_and_stops_other_checks(self):
        result = analyze_code("if True\n    print(missing)\n")
        self.assertEqual(result["status"], "syntax_error")
        self.assertEqual(result["issues"][0]["category"], "Syntax error")
        self.assertEqual(result["issues"][0]["line"], 1)
        self.assertIsNotNone(result["issues"][0]["column"])
        self.assertEqual(result["issue_count"], 1)

    def test_literal_division_by_zero(self):
        result = analyze_code("value = 10 / 0\n")
        self.assertEqual(result["issues"][0]["category"], "Division by zero")
        self.assertEqual(result["error_count"], 1)

    def test_factorial_zero_accumulator_suggests_one(self):
        result = analyze_code("""def factorial(n):
    result = 0
    for value in range(1, n + 1):
        result *= value
    return result
""")
        issue = next(item for item in result["issues"] if item["category"] == "Factorial initialization")
        self.assertIn("result = 1", issue["corrected_code"])

    def test_known_sequence_and_dictionary_problems(self):
        result = analyze_code("items = [1, 2]\nprint(items[4])\ndata = {'a': 1}\nprint(data['b'])\n")
        categories = {item["category"] for item in result["issues"]}
        self.assertIn("List index out of range", categories)
        self.assertIn("Missing dictionary key", categories)

    def test_multiple_issues_are_counted_without_duplicate_zero_division(self):
        result = analyze_code("print(missing)\na = 3 / 0\nb = 2 / 0\n")
        self.assertEqual(result["issue_count"], 3)
        self.assertEqual(result["error_count"], 2)
        self.assertEqual(result["warning_count"], 1)

    def test_obvious_constant_type_mismatch(self):
        result = analyze_code("value = 'score: ' + 10\n")
        self.assertTrue(any(item["category"] == "Incompatible types" for item in result["issues"]))

    def test_comments_strings_functions_loops_and_classes_do_not_create_name_warnings(self):
        code = """# missing_name is only a comment
text = 'another_missing_name'
def choose(value):
    selected = value
    return selected
for item in (1, 2):
    print(item)
class Sample:
    label = 'safe'
class Config:
    value = 1
    doubled = value + 1
"""
        result = analyze_code(code)
        self.assertFalse(any(issue["category"] == "Undefined variable" for issue in result["issues"]))

    def test_empty_and_non_text_input_are_handled(self):
        for value in ("", "   ", None, 42):
            with self.subTest(value=value):
                self.assertEqual(analyze_code(value)["status"], "invalid")

    def test_oversized_input_fails_gracefully(self):
        result = analyze_code("#" + "x" * MAX_SOURCE_LENGTH)
        self.assertEqual(result["status"], "analysis_failed")
        self.assertEqual(result["warning_count"], 1)

    def test_finding_count_is_bounded_and_disclosed(self):
        source = "\n".join("print(missing_{})".format(index) for index in range(MAX_ISSUES + 5))
        result = analyze_code(source)
        self.assertEqual(result["issue_count"], MAX_ISSUES + 1)
        self.assertEqual(result["issues"][-1]["category"], "Result limit")


if __name__ == "__main__":
    unittest.main()
