"""Rule-based diagnosis for common Python exception messages.

This module only inspects text. It never parses or executes submitted code.
"""

import re


# Keep this information together so the beginner-facing advice is easy to edit.
_GUIDANCE = {
    "NameError": {
        "explanation": "Python could not find a name (such as a variable or function) when it tried to use it.",
        "causes": ["The name may be misspelled.", "It may not have been assigned yet, or it may be outside the current scope."],
        "fix": "Check the spelling and capitalization, then make sure the variable or function is defined before this line.",
    },
    "TypeError": {
        "explanation": "An operation or function received a value of a kind it cannot use.",
        "causes": ["Values may have incompatible types, such as adding text to a number.", "A function may have received the wrong number or kind of arguments."],
        "fix": "Check the types and function arguments shown near the traceback line. Convert a value when appropriate, or correct the call.",
    },
    "ValueError": {
        "explanation": "The value had an acceptable general type, but its contents were not valid for the operation.",
        "causes": ["A conversion may have received text that is not a valid number.", "A function may reject a value outside its allowed format or range."],
        "fix": "Check the actual value before the failing operation and validate or correct its format.",
    },
    "IndexError": {
        "explanation": "A sequence such as a list or string was accessed at a position that does not exist.",
        "causes": ["The index may be too large or negative for the sequence.", "The sequence may be empty or shorter than expected."],
        "fix": "Check the sequence length before indexing, and remember that positions start at 0.",
    },
    "KeyError": {
        "explanation": "A dictionary lookup requested a key that is not present.",
        "causes": ["The key may be misspelled or have a different type.", "The dictionary may not contain that key for this input."],
        "fix": "Inspect the dictionary's keys, or use `.get(key)` when a missing key should have a default value.",
    },
    "ZeroDivisionError": {
        "explanation": "A division or remainder operation tried to use zero as its divisor.",
        "causes": ["The denominator may be zero.", "A calculation may have produced zero unexpectedly."],
        "fix": "Check the denominator before dividing and decide what the program should do when it is zero.",
    },
    "AttributeError": {
        "explanation": "An object does not have the attribute or method that the code tried to use.",
        "causes": ["The attribute name may be misspelled.", "The object may be a different type or have the value `None`."],
        "fix": "Check the object's type and value, then use an attribute that exists for that object.",
    },
    "ImportError": {
        "explanation": "Python found an import target, but could not import the requested name or component from it.",
        "causes": ["The requested name may not exist in that module.", "There may be a naming conflict or an incompatible package version."],
        "fix": "Check the module and imported name spelling, and confirm the name is provided by the installed package.",
    },
    "ModuleNotFoundError": {
        "explanation": "Python could not find the module named in the import.",
        "causes": ["The module name may be misspelled.", "The package may not be installed in the Python environment running the program."],
        "fix": "Check the import spelling and active environment. If it is an external package, install it in that environment using the project's approved setup steps.",
    },
    "SyntaxError": {
        "explanation": "Python could not understand the program's syntax, so it stopped before running that statement.",
        "causes": ["A bracket, quote, or colon may be missing or misplaced.", "A keyword, operator, or statement may be written in an invalid order."],
        "fix": "Look at the reported line and the line just before it; check punctuation, matching quotes/brackets, and statement structure.",
    },
}

_EXCEPTION_NAMES = tuple(sorted(_GUIDANCE, key=len, reverse=True))
_EXCEPTION_LINE = re.compile(
    r"^\s*(?P<type>" + "|".join(map(re.escape, _EXCEPTION_NAMES)) + r")\s*(?::\s*(?P<message>.*))?$"
)
# Python exception classes conventionally start with a capital letter. Do not
# require an ``Error``/``Exception`` suffix: user-defined classes such as
# ``CustomProblem`` are valid exception types too. Requiring the colon helps
# keep ordinary prose from being mistaken for an exception line.
_ANY_EXCEPTION_LINE = re.compile(
    r"^\s*((?:[A-Z][A-Za-z0-9_]*)(?:\.[A-Z][A-Za-z0-9_]*)*)\s*:\s*(.*)$"
)


def diagnose(error_text):
    """Return a beginner-friendly diagnosis for an exception or traceback string.

    The result is a dictionary with ``status``, ``error_type``, ``message``,
    ``explanation``, ``likely_causes``, and ``suggested_fix``. ``status`` is
    ``supported``, ``unknown``, ``invalid``, or ``malformed``.
    """
    if not isinstance(error_text, str) or not error_text.strip():
        return _result(
            "invalid", None, "",
            "Please paste a non-empty Python error message or traceback.",
            ["The input may be blank or may not be text."],
            "Copy the final error line from Python and try again.",
        )

    lines = [line.strip() for line in error_text.strip().splitlines() if line.strip()]
    # Tracebacks normally end with the exception line. Search backwards so
    # earlier source text that happens to mention an exception is ignored.
    for line in reversed(lines):
        match = _EXCEPTION_LINE.match(line)
        if match:
            error_type = match.group("type")
            message = (match.group("message") or "").strip()
            guide = _GUIDANCE[error_type]
            return _result("supported", error_type, message, guide["explanation"], guide["causes"], guide["fix"])

    # A syntactically traceback-like input without a recognizable final
    # exception is reported as malformed instead of guessed at.
    looks_like_traceback = any(line.startswith("Traceback (most recent call last):") for line in lines)
    looks_like_exception = any(_ANY_EXCEPTION_LINE.match(line) for line in lines)
    if looks_like_traceback and not looks_like_exception:
        return _result(
            "malformed", None, "",
            "This looks like an incomplete or malformed traceback, so its error type cannot be identified reliably.",
            ["The final exception line may be missing, cut off, or not copied."],
            "Copy the complete traceback, including its final line, and submit it again.",
        )

    # Preserve an unsupported exception name and its message when possible.
    for line in reversed(lines):
        match = _ANY_EXCEPTION_LINE.match(line)
        if match:
            return _result(
                "unknown", match.group(1), match.group(2).strip(),
                "This error type is not covered by DebugMate's current diagnosis rules.",
                ["The application may not yet have a rule for this exception."],
                "Read the traceback from the bottom upward and check the Python documentation for this exception type.",
            )

    return _result(
        "unknown", None, "",
        "DebugMate could not identify a supported Python exception in this text.",
        ["The input may be a plain description rather than an exception line.", "The traceback may be incomplete."],
        "Copy the final exception line (for example, `NameError: name 'total' is not defined`) and try again.",
    )


def _result(status, error_type, message, explanation, likely_causes, suggested_fix):
    """Build the same result shape for every outcome."""
    return {
        "status": status,
        "error_type": error_type,
        "message": message,
        "explanation": explanation,
        "likely_causes": likely_causes,
        "suggested_fix": suggested_fix,
    }
