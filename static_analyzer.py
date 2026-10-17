"""Conservative, rule-based static checks for submitted Python source.

This module parses source with :mod:`ast`; it never imports or executes it.
The checks intentionally report only cases that can be established from the
text or simple literal values. They are learning aids, not a complete linter.
"""

import ast
import builtins


MAX_SOURCE_LENGTH = 100_000
MAX_ISSUES = 100


def analyze_code(source):
    """Return a stable, beginner-friendly analysis result for Python source."""
    if not isinstance(source, str) or not source.strip():
        return _result("invalid", "Please paste some Python code to analyze.", [])
    if len(source) > MAX_SOURCE_LENGTH:
        return _result(
            "analysis_failed",
            "This submission is too large for the current analyzer (limit: 100,000 characters).",
            [_issue("Input limit", "warning", None, None, "The code was not parsed because it exceeds the safe analysis size limit.", "Submit a smaller file or analyze it in sections.")],
        )

    try:
        tree = ast.parse(source, filename="<submitted-code>")
    except SyntaxError as exc:
        line = exc.lineno
        code_line = _line_at(source, line)
        explanation = "Python could not parse this source, so the other static checks could not run."
        if exc.msg:
            explanation += " Parser message: " + exc.msg + "."
        fix = "Check punctuation and statement structure near this line; match brackets and quotes, and add required colons."
        return _result(
            "syntax_error", "Fix the syntax problem before reviewing other checks.",
            [_issue("Syntax error", "error", line, exc.offset, explanation, fix, code_line)],
            syntax_message=exc.msg,
        )
    except (ValueError, MemoryError, RecursionError) as exc:
        # These can arise from pathological parser input; exception details
        # are not echoed because they may contain implementation information.
        return _result(
            "analysis_failed", "DebugMate could not safely parse this submission.",
            [_issue("Analysis limit", "warning", None, None, "The source exceeded a parser safety limit.", "Try analyzing a smaller or less deeply nested section of code.")],
        )

    visitor = _StaticChecks(source, tree)
    visitor.run()
    if visitor.truncated:
        visitor.issues.append(_issue(
            "Result limit", "warning", None, None,
            "Only the first {} findings are shown to keep the results manageable.".format(MAX_ISSUES),
            "Review these findings first, then analyze smaller sections if you expect more issues.",
        ))
    issues = sorted(visitor.issues, key=lambda item: (item["line"] if item["line"] is not None else float("inf"), item["category"], item["column"] or 0))
    return _result("analyzed", "Analysis complete.", issues)


def _result(status, summary, issues, syntax_message=None):
    errors = sum(issue["severity"] == "error" for issue in issues)
    warnings = sum(issue["severity"] == "warning" for issue in issues)
    if status == "analyzed":
        label = "No issues detected" if not issues else "Issues found"
    elif status == "syntax_error":
        label = "Analysis incomplete: syntax error"
    elif status == "invalid":
        label = "Analysis needs input"
    else:
        label = "Analysis failed"

    if issues:
        explanation = "{} detected issue{} ({} error{}, {} warning{}).".format(
            len(issues), "" if len(issues) == 1 else "s", errors,
            "" if errors == 1 else "s", warnings,
            "" if warnings == 1 else "s",
        )
    else:
        explanation = summary
    fixes = [issue["suggested_fix"] for issue in issues]
    # These legacy fields let existing database/history code store a useful
    # summary without changing its schema. Detailed issues stay in `issues`.
    first_category = issues[0]["category"] if issues else ("SyntaxError" if status == "syntax_error" else "StaticAnalysis")
    db_status = "malformed" if status in ("syntax_error", "analysis_failed") else "supported"
    return {
        "status": status,
        "history_status": db_status,
        "error_type": first_category,
        "message": syntax_message or "",
        "summary": label,
        "explanation": explanation,
        "suggested_fix": "\n".join(fixes) if fixes else summary,
        "issues": issues,
        "issue_count": len(issues),
        "error_count": errors,
        "warning_count": warnings,
        "analysis_complete": status == "analyzed",
    }


def _issue(category, severity, line, column, explanation, suggested_fix, code_line=None, corrected_code=None):
    return {
        "category": category,
        "severity": severity,
        "line": line,
        "column": column,
        "code": code_line,
        "explanation": explanation,
        "suggested_fix": suggested_fix,
        "corrected_code": corrected_code,
    }


def _line_at(source, number):
    lines = source.splitlines()
    return lines[number - 1] if number and 0 < number <= len(lines) else None


def _literal_number(node):
    """Read simple numeric constants without evaluating arbitrary expressions."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _literal_number(node.operand)
        return value if isinstance(node.op, ast.UAdd) or value is None else -value
    return None


def _literal_value(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes, int, float, bool, type(None))):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _literal_number(node)
        return value
    return _NOT_LITERAL


_NOT_LITERAL = object()


def _target_names(target):
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        names = set()
        for child in target.elts:
            names.update(_target_names(child))
        return names
    return set()


def _bound_in_statement(statement):
    """Names bound by one statement, excluding nested function/class bodies."""
    names = set()
    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        names.add(statement.name)
        return names
    if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        for target in targets:
            names.update(_target_names(target))
    elif isinstance(statement, (ast.For, ast.AsyncFor)):
        names.update(_target_names(statement.target))
    elif isinstance(statement, (ast.With, ast.AsyncWith)):
        for item in statement.items:
            if item.optional_vars:
                names.update(_target_names(item.optional_vars))
    elif isinstance(statement, (ast.Import, ast.ImportFrom)):
        for alias in statement.names:
            names.add(alias.asname or alias.name.split(".")[0])
    elif isinstance(statement, ast.ExceptHandler) and statement.name:
        names.add(statement.name)
    return names


def _scope_bindings(statements):
    names = set()
    for statement in statements:
        stack = [statement]
        while stack:
            node = stack.pop()
            names.update(_bound_in_statement(node))
            # A nested scope's declared name belongs here; its internal
            # assignments belong to the nested scope and must not leak out.
            if node is not statement and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            if node is statement and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            stack.extend(ast.iter_child_nodes(node))
    return names


def _first_assignment_lines(statements):
    first = {}
    for statement in statements:
        stack = [statement]
        while stack:
            node = stack.pop()
            for name in _bound_in_statement(node):
                first[name] = min(first.get(name, node.lineno), node.lineno)
            if node is not statement and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            if node is statement and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            stack.extend(ast.iter_child_nodes(node))
    return first


class _StaticChecks(ast.NodeVisitor):
    def __init__(self, source, tree):
        self.source = source
        self.tree = tree
        self.issues = []
        self._seen = set()
        self.globals = _scope_bindings(tree.body)
        self.global_first_lines = _first_assignment_lines(tree.body)
        self.builtins = set(dir(builtins))
        self.scopes = []
        self.class_scopes = []
        self.truncated = False
        self.literal_sequences = {}
        self.literal_dicts = {}
        self._collect_literals()

    def run(self):
        self.visit(self.tree)
        self._check_factorial_initialization()

    def _add(self, category, severity, node, explanation, fix, corrected_code=None):
        if len(self.issues) >= MAX_ISSUES:
            self.truncated = True
            return
        line = getattr(node, "lineno", None)
        column = getattr(node, "col_offset", None)
        code_line = _line_at(self.source, line)
        key = (category, line, column, explanation)
        if key in self._seen:
            return
        self._seen.add(key)
        self.issues.append(_issue(category, severity, line, column, explanation, fix, code_line, corrected_code))

    def _collect_literals(self):
        assignment_counts = {}
        candidates = {}
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    for name in _target_names(target):
                        assignment_counts[name] = assignment_counts.get(name, 0) + 1
                        candidate = (None, None)
                        if isinstance(value, (ast.List, ast.Tuple)) and all(_literal_value(x) is not _NOT_LITERAL for x in value.elts):
                            candidate = ("sequence", len(value.elts))
                        elif isinstance(value, ast.Dict) and all(key is not None for key in value.keys):
                            keys = [_literal_value(key) for key in value.keys if key is not None]
                            if all(key is not _NOT_LITERAL for key in keys):
                                candidate = ("dictionary", set(keys))
                        candidates[name] = candidate
        # If a name is assigned more than once, its value at a use site is not
        # obvious from this intentionally small, path-insensitive analyzer.
        for name, candidate in candidates.items():
            if assignment_counts[name] == 1:
                if candidate[0] == "sequence":
                    self.literal_sequences[name] = candidate[1]
                elif candidate[0] == "dictionary":
                    self.literal_dicts[name] = candidate[1]

    def visit_Module(self, node):
        # Visit all nodes normally; bindings are collected in advance, while
        # function visitors establish their own local-name sets.
        for statement in node.body:
            self.visit(statement)

    def visit_FunctionDef(self, node):
        local_names = _scope_bindings(node.body)
        args = node.args
        for arg in args.posonlyargs + args.args + args.kwonlyargs:
            local_names.add(arg.arg)
        if args.vararg:
            local_names.add(args.vararg.arg)
        if args.kwarg:
            local_names.add(args.kwarg.arg)
        first_lines = _first_assignment_lines(node.body)
        for arg in args.posonlyargs + args.args + args.kwonlyargs:
            first_lines[arg.arg] = node.lineno
        for arg in (args.vararg, args.kwarg):
            if arg:
                first_lines[arg.arg] = node.lineno
        globals_declared = {item.name for statement in node.body for item in ast.walk(statement) if isinstance(item, ast.Global) for item in item.names}
        self.scopes.append((local_names, first_lines, globals_declared))
        # Defaults and decorators are evaluated in the enclosing scope.
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in list(node.args.defaults) + [x for x in node.args.kw_defaults if x is not None]:
            self.visit(default)
        for statement in node.body:
            self.visit(statement)
        self.scopes.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)
        self.class_scopes.append(_scope_bindings(node.body))
        for statement in node.body:
            self.visit(statement)
        self.class_scopes.pop()

    def visit_Name(self, node):
        if not isinstance(node.ctx, ast.Load):
            return
        name = node.id
        if name in self.builtins:
            return
        if self.scopes:
            local_names, first_lines, globals_declared = self.scopes[-1]
            if name in globals_declared:
                if name not in self.globals:
                    self._add("Undefined variable", "warning", node,
                              "This name is declared global but no assignment to it was found in the submitted module.",
                              "Define the global name before this function is called, or pass the value as a function argument.")
                return
            if name in local_names:
                first_line = first_lines.get(name)
                if first_line is not None and node.lineno <= first_line:
                    self._add("Use before assignment", "error", node,
                              "This function assigns to `{}` later, so Python treats it as local; this use happens before that assignment.".format(name),
                              "Assign `{}` before reading it, or pass an initial value into the function.".format(name))
                return
            if any(name in outer[0] for outer in self.scopes[:-1]):
                return
        elif self.class_scopes and name in self.class_scopes[-1]:
            return
        if name in self.globals:
            first_line = self.global_first_lines.get(name)
            if not self.scopes and first_line is not None and node.lineno <= first_line:
                self._add("Use before assignment", "error", node,
                          "`{}` is read before its first assignment in the module.".format(name),
                          "Assign `{}` before this line, or move this statement below the assignment.".format(name))
            return
        if name not in self.globals:
            self._add("Undefined variable", "warning", node,
                      "The name `{}` is used but no definition was found in the visible module or function scope.".format(name),
                      "Define `{}` before using it, or check whether its spelling should match another variable.".format(name))

    def visit_BinOp(self, node):
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and _literal_number(node.right) == 0:
            self._add("Division by zero", "error", node,
                      "The divisor is the literal zero, so this expression raises ZeroDivisionError.",
                      "Check that the divisor is not zero before dividing.")
        if isinstance(node.op, ast.Add):
            left, right = _literal_value(node.left), _literal_value(node.right)
            if ((isinstance(left, (str, bytes)) and isinstance(right, (int, float))) or
                    (isinstance(right, (str, bytes)) and isinstance(left, (int, float)))):
                self._add("Incompatible types", "error", node,
                          "This addition combines text and a number, which Python cannot add directly.",
                          "Convert one value to the intended type, or use a format string if the goal is to display both.")
        self.generic_visit(node)

    def visit_Subscript(self, node):
        index = _literal_value(node.slice)
        length = None
        keys = None
        if isinstance(node.value, (ast.List, ast.Tuple)):
            length = len(node.value.elts)
        elif isinstance(node.value, ast.Name):
            length = self.literal_sequences.get(node.value.id)
            keys = self.literal_dicts.get(node.value.id)
        if isinstance(index, int) and length is not None and not -length <= index < length:
            self._add("List index out of range", "error", node,
                      "Index {} is outside this sequence's known {} item{} (valid indexes are {} through {}).".format(
                          index, length, "" if length == 1 else "s", -length, length - 1),
                      "Use an index within the sequence length, or check its length before indexing.")
        if index is not _NOT_LITERAL and keys is not None and index not in keys:
            self._add("Missing dictionary key", "warning", node,
                      "The dictionary literal assigned here does not contain the key {!r}.".format(index),
                      "Add the key, check the spelling, or use `.get()` if a missing key should have a default.")
        if isinstance(node.value, ast.Dict) and index is not _NOT_LITERAL:
            literal_keys = {_literal_value(key) for key in node.value.keys if key is not None}
            if index not in literal_keys:
                self._add("Missing dictionary key", "warning", node,
                          "This dictionary literal does not contain the key {!r}.".format(index),
                          "Add the key, check the spelling, or use `.get()` if a missing key should have a default.")
        self.generic_visit(node)

    def visit_ListComp(self, node):
        # Comprehension scopes need their own binding model. Skip name checks
        # inside them rather than risk telling learners valid code is broken.
        self._check_expression_issues(node)

    def visit_SetComp(self, node):
        self._check_expression_issues(node)

    def visit_DictComp(self, node):
        self._check_expression_issues(node)

    def visit_GeneratorExp(self, node):
        self._check_expression_issues(node)

    def _check_expression_issues(self, node):
        for child in ast.walk(node):
            if isinstance(child, ast.BinOp):
                if isinstance(child.op, (ast.Div, ast.FloorDiv, ast.Mod)) and _literal_number(child.right) == 0:
                    self._add("Division by zero", "error", child,
                              "The divisor is the literal zero, so this expression raises ZeroDivisionError.",
                              "Check that the divisor is not zero before dividing.")
                elif isinstance(child.op, ast.Add):
                    left, right = _literal_value(child.left), _literal_value(child.right)
                    if ((isinstance(left, (str, bytes)) and isinstance(right, (int, float))) or
                            (isinstance(right, (str, bytes)) and isinstance(left, (int, float)))):
                        self._add("Incompatible types", "error", child,
                                  "This addition combines text and a number, which Python cannot add directly.",
                                  "Convert one value to the intended type, or use a format string if the goal is to display both.")

    def _check_factorial_initialization(self):
        for node in ast.walk(self.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or "factorial" not in node.name.lower():
                continue
            zero_targets = set()
            multiplication_lines = set()
            for statement in node.body:
                for child in ast.walk(statement):
                    if isinstance(child, (ast.Assign, ast.AnnAssign)):
                        targets = child.targets if isinstance(child, ast.Assign) else [child.target]
                        if _literal_number(child.value) == 0:
                            for target in targets:
                                zero_targets.update(_target_names(target))
                    if isinstance(child, (ast.AugAssign, ast.BinOp)) and isinstance(child.op if isinstance(child, ast.AugAssign) else child.op, ast.Mult):
                        if isinstance(child, ast.AugAssign):
                            multiplication_lines.update(_target_names(child.target))
                        else:
                            for part in ast.walk(child):
                                if isinstance(part, ast.Name):
                                    multiplication_lines.add(part.id)
            for statement in node.body:
                if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                    targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                    assigned = set().union(*(_target_names(target) for target in targets))
                    for name in assigned & zero_targets & multiplication_lines:
                        self._add("Factorial initialization", "warning", statement,
                                  "`{}` starts at 0 and is later multiplied; a factorial product starting at zero remains zero.".format(name),
                                  "A factorial accumulator normally starts at 1 before multiplying by each factor.",
                                  corrected_code=statement.col_offset * " " + "{} = 1".format(name))

