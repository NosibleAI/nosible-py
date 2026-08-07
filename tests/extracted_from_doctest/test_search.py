"""Tests for test search."""

import os
from typing import Any

from nosible.classes.search import Search
from nosible.classes.search_set import SearchSet

TEST_MODULE = os.path.basename(p=__file__)


def test_search_initialization() -> None:
    """

    Verify search initialization.

    :return: Test result or None.
    """
    search = Search(
        question="What is Python?",
        n_results=5,
        language="en",
        publish_start="2023-01-01",
        publish_end="2023-12-31",
        certain=True
    )
    assert search.question == "What is Python?"
    assert search.n_results == 5
    assert search.language == "en"
    assert search.publish_start == "2023-01-01"
    assert search.publish_end == "2023-12-31"
    assert search.certain is True


def test_search_to_dict_and_from_dict() -> None:
    """

    Verify search to dict and from dict.

    :return: Test result or None.
    """
    params = {
        "question": "What is Python?",
        "n_results": 10,
        "language": "en",
        "publish_start": "2023-01-01",
        "certain": True,
    }
    search = Search.from_dict(data=params)
    payload = search.to_dict()
    assert payload["question"] == "What is Python?"
    restored_search = Search.from_dict(data=payload)
    assert restored_search.question == search.question
    assert restored_search.n_results == search.n_results


def test_search_save_and_load(
    tmp_path: Any
) -> None:
    """

    Verify search save and load.

    :param tmp_path: Test dependency or input.
    :return: Test result or None.
    """
    search = Search(
        question="What is Python?",
        n_results=3,
        language="en",
        publish_start="2023-01-01"
    )
    file_path = tmp_path / "search.json"
    search.write_json(path=file_path)
    assert file_path.exists()
    loaded = Search.read_json(path=file_path)
    assert isinstance(loaded, Search)
    assert loaded.question == search.question


def test_search_addition_combines_into_searchset() -> None:
    """

    Verify search addition combines into searchset.

    :return: Test result or None.
    """
    first_search = Search(question="Q1")
    second_search = Search(question="Q2")
    combined = first_search + second_search
    assert isinstance(combined, SearchSet)
    assert len(combined.searches_list) == 2
