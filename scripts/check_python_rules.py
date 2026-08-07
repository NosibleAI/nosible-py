"""Check repository Python against the NOSIBLE project conventions."""

import os
import ast
import builtins
import io
import re
import tokenize
from pathlib import Path
from typing import FrozenSet, List, Optional, Set, Union

MODULE_NAME = os.path.basename(p=__file__)
PYTHON_PATHS = (
    Path("src"),
    Path("tests"),
    Path("scripts")
)
STANDALONE_PATHS = (
    Path("setup.py"),
    Path("docs/conf.py")
)
FUNCTION_NODE = Union[ast.FunctionDef, ast.AsyncFunctionDef]
SNAKE_CASE_PATTERN = re.compile(
    pattern=r"^[a-z][a-z0-9_]*$"
)
PASCAL_CASE_PATTERN = re.compile(
    pattern=r"^[A-Z][A-Za-z0-9]*$"
)
STDLIB_MODULES: FrozenSet[str] = frozenset(
    {
        "ast",
        "builtins",
        "calendar",
        "collections",
        "concurrent",
        "copy",
        "csv",
        "dataclasses",
        "datetime",
        "email",
        "gzip",
        "functools",
        "inspect",
        "io",
        "json",
        "logging",
        "math",
        "os",
        "pathlib",
        "re",
        "sys",
        "textwrap",
        "threading",
        "time",
        "tokenize",
        "types",
        "typing",
        "unittest",
        "urllib",
        "warnings"
    }
)
FIRST_PARTY_MODULES: FrozenSet[str] = frozenset(
    {
        "nosible",
        "scripts"
    }
)
BUILTIN_CALLS: FrozenSet[str] = frozenset(dir(builtins))
POSITIONAL_ONLY_CALLS: FrozenSet[str] = frozenset(
    {
        "AssertionError",
        "IndexError",
        "KeyError",
        "Path",
        "RuntimeError",
        "SystemExit",
        "TimeoutError",
        "TypeError",
        "ValueError",
        "all",
        "any",
        "bool",
        "callable",
        "datetime.fromisoformat",
        "dict",
        "dir",
        "divmod",
        "enumerate",
        "float",
        "frozenset",
        "getattr",
        "getattr(client.world, method_name)",
        "hasattr",
        "int",
        "isinstance",
        "iter",
        "len",
        "list",
        "math.ceil",
        "max",
        "min",
        "next",
        "os.path.exists",
        "partial",
        "pl.col",
        "pl.when",
        "print",
        "range",
        "set",
        "setattr",
        "sorted",
        "str",
        "sum",
        "time.sleep",
        "type",
        "types.MethodType"
    }
)
POSITIONAL_ONLY_METHODS: FrozenSet[str] = frozenset(
    {
        "__getattribute__",
        "__init__",
        "__setattr__",
        "addoption",
        "append",
        "endswith",
        "extend",
        "get",
        "group",
        "insert",
        "index",
        "intersection",
        "issubset",
        "join",
        "lstrip",
        "pop",
        "replace",
        "rfind",
        "rstrip",
        "setdefault",
        "startswith",
        "strip",
        "submit",
        "update",
        "with_columns",
        "write",
        "writerow"
    }
)


class RuleVisitor(ast.NodeVisitor):
    """Collect function, call, naming, and documentation violations."""

    def __init__(
        self: "RuleVisitor",
        path: Path,
        source: str,
        issues: List[str],
        callable_names: Set[str],
        method_names: Set[str]
    ) -> None:
        """
        Initialize a visitor for one Python module.

        :param path: Python module path.
        :param source: Python module source.
        :param issues: Shared issue collection.
        :param callable_names: Project function and class names.
        :param method_names: Project method names.
        :return: None.
        """
        self.path = path
        self.source = source
        self.lines = source.splitlines()
        self.issues = issues
        self.callable_names = callable_names
        self.method_names = method_names
        self.function_depth = 0

    def visit_FunctionDef(
        self: "RuleVisitor",
        node: ast.FunctionDef
    ) -> None:
        """
        Check a synchronous function and its descendants.

        :param node: Function syntax node.
        :return: None.
        """
        self.check_function(node=node)

    def visit_AsyncFunctionDef(
        self: "RuleVisitor",
        node: ast.AsyncFunctionDef
    ) -> None:
        """
        Check an asynchronous function and its descendants.

        :param node: Asynchronous function syntax node.
        :return: None.
        """
        self.check_function(node=node)

    def visit_ClassDef(
        self: "RuleVisitor",
        node: ast.ClassDef
    ) -> None:
        """
        Check a class name and class documentation.

        :param node: Class syntax node.
        :return: None.
        """
        if not PASCAL_CASE_PATTERN.fullmatch(string=node.name):
            self.record(
                node=node,
                message=f"class {node.name!r} must use PascalCase"
            )
        if ast.get_docstring(
            node=node,
            clean=False
        ) is None:
            self.record(
                node=node,
                message=f"class {node.name!r} requires a docstring"
            )
        self.generic_visit(node=node)

    def visit_Lambda(
        self: "RuleVisitor",
        node: ast.Lambda
    ) -> None:
        """
        Reject lambda expressions.

        :param node: Lambda syntax node.
        :return: None.
        """
        self.record(
            node=node,
            message="lambda expressions are not permitted"
        )
        self.generic_visit(node=node)

    def visit_Name(
        self: "RuleVisitor",
        node: ast.Name
    ) -> None:
        """
        Reject private-style local variable names.

        :param node: Name syntax node.
        :return: None.
        """
        if (
            isinstance(node.ctx, (ast.Store, ast.Del))
            and (
                (
                    node.id.startswith("_")
                    and node.id != "_"
                    and not is_dunder(name=node.id)
                )
                or (node.id != "_" and len(node.id) <= 2)
            )
        ):
            self.record(
                node=node,
                message=f"variable {node.id!r} must use a descriptive name"
            )
        self.generic_visit(node=node)

    def visit_Attribute(
        self: "RuleVisitor",
        node: ast.Attribute
    ) -> None:
        """
        Reject private-style attribute names.

        :param node: Attribute syntax node.
        :return: None.
        """
        if node.attr.startswith("_") and not is_dunder(name=node.attr):
            self.record(
                node=node,
                message=f"attribute {node.attr!r} may not start with an underscore"
            )
        self.generic_visit(node=node)

    def visit_Call(
        self: "RuleVisitor",
        node: ast.Call
    ) -> None:
        """
        Check positional arguments, keyword-call layout, and trailing commas.

        :param node: Call syntax node.
        :return: None.
        """
        if node.args:
            if is_project_call(
                node=node,
                callable_names=self.callable_names,
                method_names=self.method_names
            ):
                self.record(
                    node=node,
                    message="project calls must use keyword arguments"
                )
            elif not is_positional_only_call(node=node):
                self.record(
                    node=node,
                    message="calls must use keyword arguments"
                )
        segment = ast.get_source_segment(
            source=self.source,
            node=node
        )
        if segment is not None and segment[:-1].rstrip().endswith(","):
            self.record(
                node=node,
                message="function calls may not use a trailing comma"
            )
        if len(node.keywords) >= 2:
            keyword_lines = [
                keyword.lineno
                for keyword in node.keywords
            ]
            if (
                node.lineno in keyword_lines
                or len(keyword_lines) != len(set(keyword_lines))
            ):
                self.record(
                    node=node,
                    message="each keyword argument must start on its own line"
                )
            closing_prefix = self.lines[node.end_lineno - 1][
                : node.end_col_offset - 1
            ]
            if closing_prefix.strip():
                self.record(
                    node=node,
                    message="multi-keyword calls must close on their own line"
                )
        self.generic_visit(node=node)

    def check_function(
        self: "RuleVisitor",
        node: FUNCTION_NODE
    ) -> None:
        """
        Check one function contract and then visit its body.

        :param node: Function syntax node.
        :return: None.
        """
        if (
            not is_dunder(name=node.name)
            and not node.name.startswith("visit_")
            and not SNAKE_CASE_PATTERN.fullmatch(string=node.name)
        ):
            self.record(
                node=node,
                message=f"function {node.name!r} must use snake_case"
            )
        if self.function_depth:
            self.record(
                node=node,
                message="functions may not be nested"
            )
        arguments = function_arguments(node=node)
        docstring = ast.get_docstring(
            node=node,
            clean=False
        )
        if docstring is None:
            self.record(
                node=node,
                message=f"function {node.name!r} requires a docstring"
            )
            docstring = ""
        for argument in arguments:
            if argument.annotation is None:
                self.record(
                    node=argument,
                    message=f"parameter {argument.arg!r} requires a type"
                )
            if (
                argument.arg not in {"self", "cls"}
                and f":param {argument.arg}:" not in docstring
            ):
                self.record(
                    node=argument,
                    message=f"parameter {argument.arg!r} requires RST documentation"
                )
        if node.returns is None:
            self.record(
                node=node,
                message=f"function {node.name!r} requires a return type"
            )
        if ":return:" not in docstring:
            self.record(
                node=node,
                message=f"function {node.name!r} requires an RST return field"
            )
        check_signature_layout(
            path=self.path,
            source=self.source,
            node=node,
            arguments=arguments,
            issues=self.issues
        )
        self.function_depth += 1
        self.generic_visit(node=node)
        self.function_depth -= 1

    def record(
        self: "RuleVisitor",
        node: ast.AST,
        message: str
    ) -> None:
        """
        Add one path-and-line issue.

        :param node: Syntax node associated with the issue.
        :param message: Human-readable rule violation.
        :return: None.
        """
        self.issues.append(
            f"{self.path}:{getattr(node, 'lineno', 1)}: {message}"
        )


def main() -> int:
    """
    Check every maintained Python file and report all violations.

    :return: Zero when the repository follows the configured rules.
    """
    issues = []
    paths = discover_python_paths()
    callable_names, method_names = discover_project_callables(paths=paths)
    for path in paths:
        check_path(
            path=path,
            issues=issues,
            callable_names=callable_names,
            method_names=method_names
        )
    if issues:
        for issue in issues:
            print(issue)
        print(f"NOSIBLE Python rules failed with {len(issues)} issue(s).")
        return 1
    print("NOSIBLE Python rules passed.")
    return 0


def discover_python_paths() -> List[Path]:
    """
    Return every maintained Python path in deterministic order.

    :return: Sorted Python module paths.
    """
    paths = [
        path
        for root in PYTHON_PATHS
        for path in root.rglob(pattern="*.py")
    ]
    paths.extend(STANDALONE_PATHS)
    return sorted(paths)


def discover_project_callables(
    paths: List[Path]
) -> tuple[Set[str], Set[str]]:
    """
    Return project function, class, and method names across maintained files.

    :param paths: Maintained Python paths.
    :return: Project callable names and method names.
    """
    callable_names = set()
    method_names = set()
    for path in paths:
        tree = ast.parse(
            source=path.read_text(encoding="utf-8"),
            filename=str(path)
        )
        path_callable_names, path_method_names = tree_callables(tree=tree)
        callable_names.update(path_callable_names)
        method_names.update(path_method_names)
    return callable_names, method_names


def check_path(
    path: Path,
    issues: List[str],
    callable_names: Optional[Set[str]] = None,
    method_names: Optional[Set[str]] = None
) -> None:
    """
    Check one Python file.

    :param path: Python file to inspect.
    :param issues: Shared issue collection.
    :param callable_names: Optional project function and class names.
    :param method_names: Optional project method names.
    :return: None.
    """
    source = path.read_text(encoding="utf-8")
    check_comments(
        path=path,
        source=source,
        issues=issues
    )
    try:
        tree = ast.parse(
            source=source,
            filename=str(path)
        )
    except SyntaxError as error:
        issues.append(f"{path}:{error.lineno or 1}: {error.msg}")
        return
    local_callable_names, local_method_names = tree_callables(tree=tree)
    active_callable_names = (
        callable_names
        if callable_names is not None
        else local_callable_names
    )
    active_method_names = (
        method_names
        if method_names is not None
        else local_method_names
    )
    check_module_layout(
        path=path,
        source=source,
        tree=tree,
        issues=issues
    )
    check_declaration_order(
        path=path,
        tree=tree,
        issues=issues
    )
    visitor = RuleVisitor(
        path=path,
        source=source,
        issues=issues,
        callable_names=active_callable_names,
        method_names=active_method_names
    )
    visitor.visit(node=tree)


def check_comments(
    path: Path,
    source: str,
    issues: List[str]
) -> None:
    """
    Reject comments that do not explicitly document a non-obvious rationale.

    :param path: Python module path.
    :param source: Python module source.
    :param issues: Shared issue collection.
    :return: None.
    """
    tokens = tokenize.generate_tokens(
        readline=io.StringIO(initial_value=source).readline
    )
    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue
        if (
            token.string.startswith("# WHY:")
            and not is_commented_code(comment=token.string[6:].strip())
        ):
            continue
        issues.append(
            f"{path}:{token.start[0]}: comments must explain non-obvious "
            "intent with '# WHY:'; commented-out code is forbidden"
        )


def is_commented_code(
    comment: str
) -> bool:
    """
    Return whether a rationale comment contains executable Python syntax.

    :param comment: Comment text following the rationale prefix.
    :return: Whether the text contains executable syntax.
    """
    try:
        tree = ast.parse(source=comment)
    except SyntaxError:
        return False
    return any(
        isinstance(
            node,
            (
                ast.Assign,
                ast.AugAssign,
                ast.Call,
                ast.Delete,
                ast.Import,
                ast.ImportFrom,
                ast.NamedExpr,
                ast.Raise,
                ast.Return
            )
        )
        for node in ast.walk(node=tree)
    )


def tree_callables(
    tree: ast.Module
) -> tuple[Set[str], Set[str]]:
    """
    Return function, class, and method names declared in one syntax tree.

    :param tree: Parsed Python module.
    :return: Callable names and method names.
    """
    callable_names = set()
    method_names = set()
    for node in ast.walk(node=tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            callable_names |= {node.name}
            method_names |= {node.name}
        elif isinstance(node, ast.ClassDef):
            callable_names |= {node.name}
    return callable_names, method_names


def check_module_layout(
    path: Path,
    source: str,
    tree: ast.Module,
    issues: List[str]
) -> None:
    """
    Check module documentation, imports, globals, and declaration order.

    :param path: Python module path.
    :param source: Python module source.
    :param tree: Parsed Python module.
    :param issues: Shared issue collection.
    :return: None.
    """
    body = tree.body
    if not body or not is_string_expression(node=body[0]):
        issues.append(f"{path}:1: module requires a top-level docstring")
        return
    first_statement = body[1] if len(body) > 1 else None
    if not is_os_import(node=first_statement):
        issues.append(f"{path}:1: import os must immediately follow the docstring")
    check_import_contract(
        path=path,
        source=source,
        tree=tree,
        issues=issues
    )
    imports_finished = False
    classes_started = False
    functions_started = False
    for statement in body[1:]:
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            if imports_finished:
                issues.append(
                    f"{path}:{statement.lineno}: imports must remain at module top"
                )
            if isinstance(statement, ast.ImportFrom) and statement.level:
                issues.append(
                    f"{path}:{statement.lineno}: relative imports are not permitted"
                )
            continue
        imports_finished = True
        for nested_statement in ast.walk(node=statement):
            if isinstance(nested_statement, (ast.Import, ast.ImportFrom)):
                issues.append(
                    f"{path}:{nested_statement.lineno}: imports must remain at module top"
                )
        if isinstance(statement, ast.ClassDef):
            classes_started = True
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions_started = True
        if isinstance(statement, ast.ClassDef) and functions_started:
            issues.append(
                f"{path}:{statement.lineno}: classes must precede module functions"
            )
        if (
            isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign))
            and (classes_started or functions_started)
        ):
            issues.append(
                f"{path}:{statement.lineno}: module globals must precede classes and functions"
            )
        if path.as_posix() != "docs/conf.py":
            check_global_names(
                path=path,
                statement=statement,
                issues=issues
            )
    for index, statement in enumerate(body):
        if is_main_guard(node=statement) and index != len(body) - 1:
            issues.append(
                f"{path}:{statement.lineno}: __main__ guard must be the final statement"
            )
    check_top_level_spacing(
        path=path,
        body=body,
        issues=issues
    )


def check_top_level_spacing(
    path: Path,
    body: List[ast.stmt],
    issues: List[str]
) -> None:
    """
    Require two blank lines before every top-level class or function.

    :param path: Python module path.
    :param body: Top-level module statements.
    :param issues: Shared issue collection.
    :return: None.
    """
    for index, statement in enumerate(body):
        if not isinstance(
            statement,
            (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        if index == 0:
            continue
        start_line = min(
            [
                statement.lineno,
                *(
                    decorator.lineno
                    for decorator in statement.decorator_list
                )
            ]
        )
        previous_statement = body[index - 1]
        blank_lines = start_line - previous_statement.end_lineno - 1
        if blank_lines < 2:
            issues.append(
                f"{path}:{start_line}: top-level definitions require two blank lines"
            )


def check_import_contract(
    path: Path,
    source: str,
    tree: ast.Module,
    issues: List[str]
) -> None:
    """
    Check import aliasing, duplication, grouping, and group whitespace.

    :param path: Python module path.
    :param source: Python module source.
    :param tree: Parsed Python module.
    :param issues: Shared issue collection.
    :return: None.
    """
    imports = [
        statement
        for statement in tree.body
        if isinstance(statement, (ast.Import, ast.ImportFrom))
    ]
    seen_imports = set()
    previous_category = None
    previous_import = None
    for statement in imports:
        category = import_category(statement=statement)
        if previous_category is not None and category < previous_category:
            issues.append(
                f"{path}:{statement.lineno}: imports must be grouped "
                "stdlib, third-party, then first-party"
            )
        if previous_import is not None:
            expected_gap = 1 if category == previous_category else 2
            actual_gap = statement.lineno - previous_import.end_lineno
            if actual_gap != expected_gap:
                issues.append(
                    f"{path}:{statement.lineno}: import groups require exact blank-line separation"
                )
        previous_category = category
        previous_import = statement
        for alias in statement.names:
            if isinstance(statement, ast.ImportFrom) and alias.asname is not None:
                issues.append(
                    f"{path}:{statement.lineno}: imported functions, classes, "
                    "and constants may not be aliased"
                )
            import_key = (
                getattr(statement, "module", None),
                getattr(statement, "level", 0),
                alias.name,
                alias.asname
            )
            if import_key in seen_imports:
                issues.append(
                    f"{path}:{statement.lineno}: duplicate import {alias.name!r}"
                )
            seen_imports |= {import_key}


def import_category(
    statement: Union[ast.Import, ast.ImportFrom]
) -> int:
    """
    Return the required ordering category for one import statement.

    :param statement: Import syntax node.
    :return: Zero for stdlib, one for third-party, or two for first-party.
    """
    module_name = (
        statement.module
        if isinstance(statement, ast.ImportFrom)
        else statement.names[0].name
    )
    root_name = (module_name or "").split(sep=".")[0]
    if root_name in STDLIB_MODULES:
        return 0
    if root_name in FIRST_PARTY_MODULES:
        return 2
    return 1


def check_declaration_order(
    path: Path,
    tree: ast.Module,
    issues: List[str]
) -> None:
    """
    Check that local callers appear before the functions they call.

    :param path: Python module path.
    :param tree: Parsed Python module.
    :param issues: Shared issue collection.
    :return: None.
    """
    module_functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    check_function_order(
        path=path,
        functions=module_functions,
        owner=None,
        issues=issues
    )
    for class_node in (
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    ):
        methods = {
            node.name: node
            for node in class_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        check_function_order(
            path=path,
            functions=methods,
            owner=class_node.name,
            issues=issues
        )


def check_function_order(
    path: Path,
    functions: dict[str, FUNCTION_NODE],
    owner: Optional[str],
    issues: List[str]
) -> None:
    """
    Check caller-before-callee order for one function or method collection.

    :param path: Python module path.
    :param functions: Functions sharing one module or class scope.
    :param owner: Optional class name for a method collection.
    :param issues: Shared issue collection.
    :return: None.
    """
    reported_pairs = set()
    for caller in functions.values():
        for node in ast.walk(node=caller):
            callee_name = local_callee_name(
                node=node,
                owner=owner
            )
            if callee_name not in functions:
                continue
            callee = functions[callee_name]
            pair = (caller.name, callee.name)
            if (
                caller is callee
                or caller.lineno < callee.lineno
                or pair in reported_pairs
            ):
                continue
            reported_pairs |= {pair}
            label = f"{owner}.{caller.name}" if owner else caller.name
            issues.append(
                f"{path}:{caller.lineno}: caller {label!r} must appear "
                f"before callee {callee.name!r}"
            )


def local_callee_name(
    node: ast.AST,
    owner: Optional[str]
) -> Optional[str]:
    """
    Return a same-scope callee name from one syntax node.

    :param node: Candidate syntax node.
    :param owner: Optional class name for method inspection.
    :return: Same-scope callee name when present.
    """
    if not isinstance(node, ast.Call):
        return None
    if owner is None and isinstance(node.func, ast.Name):
        return node.func.id
    if owner is None or not isinstance(node.func, ast.Attribute):
        return None
    receiver = node.func.value
    if isinstance(receiver, ast.Name) and receiver.id in {
        "self",
        "cls",
        owner
    }:
        return node.func.attr
    return None


def check_global_names(
    path: Path,
    statement: ast.stmt,
    issues: List[str]
) -> None:
    """
    Check module-level assignments for constant-style names.

    :param path: Python module path.
    :param statement: Module-level statement.
    :param issues: Shared issue collection.
    :return: None.
    """
    targets = []
    if isinstance(statement, ast.Assign):
        targets.extend(statement.targets)
    elif isinstance(statement, ast.AnnAssign):
        targets.append(statement.target)
    for target in targets:
        for name_node in ast.walk(node=target):
            if not isinstance(name_node, ast.Name):
                continue
            name = name_node.id
            if (
                name == "pytestmark"
                or name.isupper()
                or is_dunder(name=name)
                or PASCAL_CASE_PATTERN.fullmatch(string=name)
            ):
                continue
            issues.append(
                f"{path}:{statement.lineno}: global {name!r} must use UPPER_SNAKE_CASE"
            )


def check_signature_layout(
    path: Path,
    source: str,
    node: FUNCTION_NODE,
    arguments: List[ast.arg],
    issues: List[str]
) -> None:
    """
    Check parameter lines, signature closing, and trailing commas.

    :param path: Python module path.
    :param source: Python module source.
    :param node: Function syntax node.
    :param arguments: Flattened function arguments.
    :param issues: Shared issue collection.
    :return: None.
    """
    if not arguments:
        return
    argument_lines = [
        argument.lineno
        for argument in arguments
    ]
    if (
        node.lineno in argument_lines
        or len(argument_lines) != len(set(argument_lines))
    ):
        issues.append(
            f"{path}:{node.lineno}: each parameter must start on its own line"
        )
    positions = signature_parentheses(
        source=source,
        node=node
    )
    if positions is None:
        issues.append(f"{path}:{node.lineno}: could not inspect function signature")
        return
    opening_end, closing_start = positions
    inner = source[opening_end:closing_start]
    if inner.rstrip().endswith(","):
        issues.append(
            f"{path}:{node.lineno}: signatures may not use a trailing comma"
        )
    closing_line_start = source.rfind("\n", 0, closing_start) + 1
    if source[closing_line_start:closing_start].strip():
        issues.append(
            f"{path}:{node.lineno}: function signatures must close on their own line"
        )


def signature_parentheses(
    source: str,
    node: FUNCTION_NODE
) -> Optional[tuple[int, int]]:
    """
    Locate absolute offsets for one function's signature parentheses.

    :param source: Python module source.
    :param node: Function syntax node.
    :return: Opening-end and closing-start offsets, when found.
    """
    tokens = list(
        tokenize.generate_tokens(
            readline=io.StringIO(initial_value=source).readline
        )
    )
    opening_index = None
    for index, token in enumerate(tokens):
        if (
            token.type == tokenize.NAME
            and token.string == "def"
            and token.start[0] == node.lineno
        ):
            opening_index = find_opening_parenthesis(
                tokens=tokens,
                start=index
            )
            break
    if opening_index is None:
        return None
    closing_index = find_closing_parenthesis(
        tokens=tokens,
        opening_index=opening_index
    )
    if closing_index is None:
        return None
    offsets = line_offsets(source=source)
    opening_end = absolute_offset(
        offsets=offsets,
        position=tokens[opening_index].end
    )
    closing_start = absolute_offset(
        offsets=offsets,
        position=tokens[closing_index].start
    )
    return opening_end, closing_start


def find_opening_parenthesis(
    tokens: List[tokenize.TokenInfo],
    start: int
) -> Optional[int]:
    """
    Find a function signature's opening parenthesis token.

    :param tokens: Tokenized Python module.
    :param start: Function-definition token index.
    :return: Opening token index, when found.
    """
    for index in range(start, len(tokens)):
        token = tokens[index]
        if token.type == tokenize.OP and token.string == "(":
            return index
    return None


def find_closing_parenthesis(
    tokens: List[tokenize.TokenInfo],
    opening_index: int
) -> Optional[int]:
    """
    Find the closing token paired with a signature opening token.

    :param tokens: Tokenized Python module.
    :param opening_index: Opening parenthesis token index.
    :return: Closing token index, when found.
    """
    depth = 0
    for index in range(
        opening_index,
        len(tokens)
    ):
        token = tokens[index]
        if token.type == tokenize.OP and token.string in "([{":
            depth += 1
        elif token.type == tokenize.OP and token.string in ")]}":
            depth -= 1
            if depth == 0:
                return index
    return None


def function_arguments(
    node: FUNCTION_NODE
) -> List[ast.arg]:
    """
    Flatten every supported function parameter category.

    :param node: Function syntax node.
    :return: Function parameters in declaration order.
    """
    arguments = list(node.args.posonlyargs)
    arguments.extend(node.args.args)
    if node.args.vararg is not None:
        arguments.append(node.args.vararg)
    arguments.extend(node.args.kwonlyargs)
    if node.args.kwarg is not None:
        arguments.append(node.args.kwarg)
    return arguments


def line_offsets(
    source: str
) -> List[int]:
    """
    Return absolute starting offsets for source lines.

    :param source: Python module source.
    :return: Absolute source offsets.
    """
    offsets = []
    total = 0
    for line in source.splitlines(keepends=True):
        offsets.append(total)
        total += len(line)
    return offsets


def absolute_offset(
    offsets: List[int],
    position: tuple[int, int]
) -> int:
    """
    Convert a token position to an absolute source offset.

    :param offsets: Absolute source line offsets.
    :param position: One-based line and zero-based column.
    :return: Absolute source offset.
    """
    line, column = position
    return offsets[line - 1] + column


def is_project_call(
    node: ast.Call,
    callable_names: Set[str],
    method_names: Set[str]
) -> bool:
    """
    Return whether a call targets a project-defined callable.

    :param node: Function-call syntax node.
    :param callable_names: Project function and class names.
    :param method_names: Project method names.
    :return: Whether keyword-only project-call rules apply.
    """
    if isinstance(node.func, ast.Name):
        return (
            node.func.id not in BUILTIN_CALLS
            and node.func.id in callable_names
        )
    if not isinstance(node.func, ast.Attribute):
        return False
    receiver = node.func.value
    if (
        isinstance(receiver, ast.Call)
        and isinstance(receiver.func, ast.Name)
        and receiver.func.id == "super"
    ):
        return False
    return node.func.attr in method_names


def is_positional_only_call(
    node: ast.Call
) -> bool:
    """
    Return whether a call is a documented exception to keyword-only calls.

    :param node: Function-call syntax node.
    :return: Whether the call requires positional arguments.
    """
    call_name = ast.unparse(ast_obj=node.func)
    if call_name in POSITIONAL_ONLY_CALLS:
        return True
    if isinstance(node.func, ast.Attribute):
        return node.func.attr in POSITIONAL_ONLY_METHODS
    return False


def is_main_guard(
    node: ast.stmt
) -> bool:
    """
    Return whether a statement is an ``if __name__ == "__main__"`` guard.

    :param node: Candidate module statement.
    :return: Whether the statement is a main-entry guard.
    """
    if not isinstance(node, ast.If):
        return False
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def is_string_expression(
    node: ast.stmt
) -> bool:
    """
    Return whether a statement is a string expression.

    :param node: Module statement.
    :return: Whether the statement contains a string constant.
    """
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def is_os_import(
    node: Optional[ast.stmt]
) -> bool:
    """
    Return whether a statement is exactly ``import os``.

    :param node: Module statement.
    :return: Whether the statement imports only ``os``.
    """
    return (
        isinstance(node, ast.Import)
        and len(node.names) == 1
        and node.names[0].name == "os"
        and node.names[0].asname is None
    )


def is_dunder(
    name: str
) -> bool:
    """
    Return whether a name is a double-underscore protocol name.

    :param name: Python identifier.
    :return: Whether the name starts and ends with two underscores.
    """
    return name.startswith("__") and name.endswith("__")


if __name__ == "__main__":
    raise SystemExit(main())
