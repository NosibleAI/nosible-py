"""Tests for test snippet."""

import os
import json
from typing import Any

import pytest

from nosible.classes.snippet import Snippet
from nosible.classes.snippet_set import SnippetSet

TEST_MODULE = os.path.basename(p=__file__)


def test_snippet_initialization_and_attrs(
    snippets_data: Any
) -> None:
    """

    Verify snippet initialization and attrs.

    :param snippets_data: Test dependency or input.
    :return: Test result or None.
    """
    assert isinstance(snippets_data, SnippetSet)
    for snippet in snippets_data:
        assert isinstance(snippet, Snippet)
        assert isinstance(snippet.content, str)


def test_snippet_getitem_and_str(
    snippets_data: Any
) -> None:
    """

    Verify snippet getitem and str.

    :param snippets_data: Test dependency or input.
    :return: Test result or None.
    """
    snippet_set = snippets_data
    if len(snippet_set) == 0:
        pytest.skip(reason="no snippets to test getitem/str")
    snippet = snippet_set[0]
    assert snippet["content"] == snippet.content
    with pytest.raises(expected_exception=KeyError):
        _ = snippet["nonexistent_field"]


def test_snippet_to_dict_and_json(
    snippets_data: Any
) -> None:
    """

    Verify snippet to dict and json.

    :param snippets_data: Test dependency or input.
    :return: Test result or None.
    """
    snippet_set = snippets_data
    if len(snippet_set) == 0:
        pytest.skip(reason="no snippets to test to_dict/write_json")
    snippet = snippet_set[0]
    payload = snippet.to_dict()
    assert isinstance(payload, dict) and "content" in payload
    json_text = snippet.write_json()
    assert json.loads(s=json_text) == payload
