"""Contracts for the repository-specific Python rules checker."""

import os
from typing import Any

from scripts.check_python_rules import check_path

TEST_MODULE = os.path.basename(p=__file__)


def test_python_rules_checker_accepts_compliant_module(
    tmp_path: Any
) -> None:
    """
    Verify the custom checker accepts a representative compliant module.

    :param tmp_path: Temporary test directory.
    :return: None.
    """
    source = '''"""Compliant sample module."""

import os


MODULE_NAME = os.path.basename(p=__file__)


class Example:
    """Representative compliant class."""

    def render(
        self: "Example",
        value: int
    ) -> str:
        """
        Render one value.

        :param value: Value to render.
        :return: Rendered value.
        """
        return str(value)
'''
    path = tmp_path / "compliant.py"
    path.write_text(
        data=source,
        encoding="utf-8"
    )
    issues: list[str] = []

    check_path(
        path=path,
        issues=issues
    )

    assert issues == []


def test_python_rules_checker_rejects_reported_style_drift(
    tmp_path: Any
) -> None:
    """
    Verify the checker catches the style categories found by red-team review.

    :param tmp_path: Temporary test directory.
    :return: None.
    """
    source = '''"""Noncompliant sample module."""

import os


MODULE_NAME = os.path.basename(p=__file__)


class Example:
    """Representative noncompliant class."""

    def render(self, value):
        self._lock = value
        transform = lambda item: item
        return dict(one=1, two=2)
'''
    path = tmp_path / "noncompliant.py"
    path.write_text(
        data=source,
        encoding="utf-8"
    )
    issues: list[str] = []

    check_path(
        path=path,
        issues=issues
    )

    expected_fragments = {
        "parameter 'self' requires a type",
        "parameter 'value' requires a type",
        "requires a return type",
        "requires a docstring",
        "each parameter must start on its own line",
        "attribute '_lock'",
        "lambda expressions are not permitted",
        "each keyword argument must start on its own line",
        "multi-keyword calls must close on their own line"
    }
    for fragment in expected_fragments:
        assert any(
            fragment in issue
            for issue in issues
        ), fragment


def test_python_rules_checker_rejects_enforcement_false_negatives(
    tmp_path: Any
) -> None:
    """
    Verify the checker rejects positional calls, nested imports, and ordering.

    :param tmp_path: Temporary test directory.
    :return: None.
    """
    source = '''"""Noncompliant enforcement sample."""

import os
from pathlib import Path as ProjectPath


MODULE_NAME = os.path.basename(p=__file__)


def leaf(
    value: int
) -> int:
    """
    Return one value.

    :param value: Value to return.
    :return: Original value.
    """
    return value


def caller(
    value: int
) -> int:
    """
    Call the earlier leaf incorrectly.

    :param value: Value to forward.
    :return: Forwarded value.
    """
    import json

    json.dumps(obj=value)
    os.fspath("value")
    # leaf(value=value)
    ProjectPath(value)
    return leaf(value)
'''
    path = tmp_path / "false_negatives.py"
    path.write_text(
        data=source,
        encoding="utf-8"
    )
    issues: list[str] = []

    check_path(
        path=path,
        issues=issues
    )

    expected_fragments = {
        "may not be aliased",
        "imports must remain at module top",
        "project calls must use keyword arguments",
        "calls must use keyword arguments",
        "commented-out code is forbidden",
        "caller 'caller' must appear before callee 'leaf'"
    }
    for fragment in expected_fragments:
        assert any(
            fragment in issue
            for issue in issues
        ), fragment


def test_python_rules_checker_rejects_import_group_drift(
    tmp_path: Any
) -> None:
    """
    Verify the checker rejects import category and spacing drift.

    :param tmp_path: Temporary test directory.
    :return: None.
    """
    source = '''"""Noncompliant import sample."""

import os

import pytest
import json
import json

import nosible
'''
    path = tmp_path / "import_drift.py"
    path.write_text(
        data=source,
        encoding="utf-8"
    )
    issues: list[str] = []

    check_path(
        path=path,
        issues=issues
    )

    assert any(
        "imports must be grouped" in issue
        for issue in issues
    )
    assert any(
        "duplicate import" in issue
        for issue in issues
    )


def test_python_rules_checker_rejects_module_declaration_drift(
    tmp_path: Any
) -> None:
    """
    Verify the checker rejects classes and globals outside their fixed blocks.

    :param tmp_path: Temporary test directory.
    :return: None.
    """
    source = '''"""Noncompliant declaration sample."""

import os


MODULE_NAME = os.path.basename(p=__file__)


def render() -> None:
    """
    Render nothing.

    :return: None.
    """


class Example:
    """Class declared after the function block."""


LATE_GLOBAL = "late"
'''
    path = tmp_path / "declaration_drift.py"
    path.write_text(
        data=source,
        encoding="utf-8"
    )
    issues: list[str] = []

    check_path(
        path=path,
        issues=issues
    )

    assert any(
        "classes must precede module functions" in issue
        for issue in issues
    )
    assert any(
        "module globals must precede classes and functions" in issue
        for issue in issues
    )


def test_python_rules_checker_rejects_unknown_positional_calls_and_spacing(
    tmp_path: Any
) -> None:
    """
    Verify positional calls and top-level spacing fail closed.

    :param tmp_path: Temporary test directory.
    :return: None.
    """
    source = '''"""Noncompliant positional and spacing sample."""

import os
from datetime import datetime


MODULE_NAME = os.path.basename(p=__file__)


def first() -> str:
    """
    Return a formatted timestamp.

    :return: Formatted timestamp.
    """
    return datetime.now().strftime("%Y-%m-%d")

def second() -> None:
    """
    Return nothing.

    :return: None.
    """
'''
    path = tmp_path / "positional_spacing.py"
    path.write_text(
        data=source,
        encoding="utf-8"
    )
    issues: list[str] = []

    check_path(
        path=path,
        issues=issues
    )

    assert any(
        "calls must use keyword arguments" in issue
        for issue in issues
    )
    assert any(
        "two blank lines" in issue
        for issue in issues
    )


def test_python_rules_checker_rejects_commented_code_with_why_prefix(
    tmp_path: Any
) -> None:
    """
    Verify the rationale prefix cannot disguise commented-out code.

    :param tmp_path: Temporary test directory.
    :return: None.
    """
    source = '''"""Noncompliant disguised code sample."""

import os


MODULE_NAME = os.path.basename(p=__file__)


def render() -> None:
    """
    Return nothing.

    :return: None.
    """
    # WHY: os.fspath(path="dead")
'''
    path = tmp_path / "commented_code.py"
    path.write_text(
        data=source,
        encoding="utf-8"
    )
    issues: list[str] = []

    check_path(
        path=path,
        issues=issues
    )

    assert any(
        "commented-out code is forbidden" in issue
        for issue in issues
    )
