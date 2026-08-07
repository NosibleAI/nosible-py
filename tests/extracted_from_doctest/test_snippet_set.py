"""Tests for test snippet set."""

import os
import json
from typing import Any

import pytest

from nosible.classes.snippet_set import SnippetSet

TEST_MODULE = os.path.basename(p=__file__)


def test_snippetset_len_getitem_index_error(
    snippets_data: Any
) -> None:
    """

    Verify snippetset len getitem index error.

    :param snippets_data: Test dependency or input.
    :return: Test result or None.
    """
    snippet_set = snippets_data
    assert len(snippet_set) == snippet_set.__len__()
    if len(snippet_set) > 0:
        assert isinstance(snippet_set[0], type(snippet_set[0]))
    with pytest.raises(expected_exception=IndexError):
        _ = snippet_set[len(snippet_set)]


def test_snippetset_iteration_and_str_reset(
    snippets_data: Any
) -> None:
    """

    Verify snippetset iteration and str reset.

    :param snippets_data: Test dependency or input.
    :return: Test result or None.
    """
    snippet_set = snippets_data
    contents = [snippet.content for snippet in snippet_set]
    assert contents == [snippet.content for snippet in snippet_set]
    iterator = iter(snippet_set)
    result = []
    with pytest.raises(expected_exception=StopIteration):
        for _ in range(len(snippet_set) + 1):
            result.append(next(iterator))
    assert len(result) == len(contents)


def test_snippetset_to_dict_and_json_roundtrip(
    snippets_data: Any
) -> None:
    """

    Verify snippetset to dict and json roundtrip.

    :param snippets_data: Test dependency or input.
    :return: Test result or None.
    """
    snippet_set = snippets_data
    payload = snippet_set.to_dict()
    assert isinstance(payload, dict)
    for inner in payload.values():
        assert isinstance(inner, dict) and "content" in inner
    json_text = snippet_set.write_json()
    assert json.loads(s=json_text) == payload
    rebuilt = SnippetSet.from_dict(data=payload)
    assert [snippet.content for snippet in rebuilt] == [snippet.content for snippet in snippet_set]
