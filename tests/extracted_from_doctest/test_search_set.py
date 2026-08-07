"""Tests for test search set."""

import os
from typing import Any

from nosible.classes.search import Search
from nosible.classes.search_set import SearchSet

TEST_MODULE = os.path.basename(p=__file__)


def test_searchset_basic_operations(
    tmp_path: Any
) -> None:
    """

    Verify searchset basic operations.

    :param tmp_path: Test dependency or input.
    :return: Test result or None.
    """
    first_search = Search(
        question="What is Python?",
        n_results=3
    )
    second_search = Search(
        question="What is PEP8?",
        n_results=2
    )
    search_set = SearchSet(searches_list=[first_search, second_search])

    lines = str(search_set).splitlines()
    assert lines[0].startswith("0: What is Python?")
    assert lines[1].startswith("1: What is PEP8?")

    third_search = Search(
        question="What is AI?",
        n_results=1
    )
    search_set.add(search=third_search)
    assert len(search_set) == 3 and search_set[2].question == "What is AI?"
    search_set.remove(index=1)
    assert [search.question for search in search_set.searches_list] == ["What is Python?", "What is AI?"]

    dicts = search_set.to_dicts()
    assert isinstance(dicts, list) and dicts[0]["question"] == "What is Python?"
    json_text = search_set.write_json()
    assert isinstance(json_text, str)
    search_set.write_json(path=tmp_path / "searches.json")
    loaded = SearchSet.read_json(path=tmp_path / "searches.json")
    loaded_questions = [
        search.question
        for search in loaded.searches_list
    ]
    expected_questions = [
        search.question
        for search in search_set.searches_list
    ]
    assert loaded_questions == expected_questions
