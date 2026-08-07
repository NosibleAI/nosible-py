"""Tests for test 04 snippets."""

import os
from typing import Any

from nosible import Snippet, SnippetSet

TEST_MODULE = os.path.basename(p=__file__)


def test_snippet_initialization(
    snippets_data: Any
) -> None:
    """

    Verify snippet initialization.

    :param snippets_data: Test dependency or input.
    :return: Test result or None.
    """
    assert isinstance(snippets_data, SnippetSet)

    assert all(isinstance(snippet, Snippet) for snippet in snippets_data)
    if len(snippets_data) > 0:
        assert isinstance(snippets_data[0], Snippet)
        assert isinstance(snippets_data[-1], Snippet)
    if len(snippets_data) > 0:
        assert isinstance(snippets_data[0].content, str)


def test_snippet_set_to_dict(
    snippets_data: Any
) -> None:
    """

    Verify snippet set to dict.

    :param snippets_data: Test dependency or input.
    :return: Test result or None.
    """
    dicts = snippets_data.to_dict()
    assert isinstance(dicts, dict)
    assert all(isinstance(snippet_payload, dict) for snippet_payload in dicts.values())
    assert all("content" in snippet_payload for snippet_payload in dicts.values())
