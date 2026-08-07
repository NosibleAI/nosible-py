"""Tests for test 03 search searchset."""

import os
from typing import Any

import pytest

from nosible import Search, SearchSet

TEST_MODULE = os.path.basename(p=__file__)

FIRST_SEARCH = Search(
    question="Hedge funds seek to expand into private credit",
    n_results=10
)
SECOND_SEARCH = Search(
    question="Nvidia insiders dump more than $1 billion in stock",
    n_results=10
)


def test_search_initialization() -> None:
    """

    Verify search initialization.

    :return: Test result or None.
    """
    assert isinstance(FIRST_SEARCH, Search)
    assert isinstance(SECOND_SEARCH, Search)
    assert FIRST_SEARCH.question == "Hedge funds seek to expand into private credit"
    assert SECOND_SEARCH.question == "Nvidia insiders dump more than $1 billion in stock"


def test_searchset_initialization() -> None:
    """

    Verify searchset initialization.

    :return: Test result or None.
    """
    search_set = SearchSet(searches_list=[FIRST_SEARCH, SECOND_SEARCH])

    assert isinstance(search_set, SearchSet)
    assert len(search_set) == 2
    assert search_set[0] == FIRST_SEARCH
    assert search_set[1] == SECOND_SEARCH
    assert search_set.searches_list== [FIRST_SEARCH, SECOND_SEARCH]


def test_searchset_iterable() -> None:
    """

    Verify searchset iterable.

    :return: Test result or None.
    """
    search_set = SearchSet(searches_list=[FIRST_SEARCH, SECOND_SEARCH])

    assert isinstance(search_set, SearchSet)
    assert all(isinstance(search, Search) for search in search_set)


def test_searchset_access() -> None:
    """

    Verify searchset access.

    :return: Test result or None.
    """
    search_set = SearchSet(searches_list=[FIRST_SEARCH, SECOND_SEARCH])
    assert search_set[0] == FIRST_SEARCH
    assert search_set[1] == SECOND_SEARCH

    with pytest.raises(expected_exception=IndexError):
        _ = search_set[2]


def test_searchset_to_dicts() -> None:
    """

    Verify searchset to dicts.

    :return: Test result or None.
    """
    search_set = SearchSet(searches_list=[FIRST_SEARCH, SECOND_SEARCH])

    dicts = search_set.to_dicts()
    assert isinstance(dicts, list)
    assert len(dicts) == 2
    assert dicts[0] == FIRST_SEARCH.to_dict()
    assert dicts[1] == SECOND_SEARCH.to_dict()


def test_searchset_write_json(
    tmp_path: Any
) -> None:
    """

    Verify searchset write json.

    :param tmp_path: Test dependency or input.
    :return: Test result or None.
    """
    search_set = SearchSet(searches_list=[FIRST_SEARCH, SECOND_SEARCH])

    json_str = search_set.write_json()
    assert isinstance(json_str, str)
    assert len(json_str) > 0

    search_set.write_json(path=tmp_path / "search_set.json")
    search_set_copy = SearchSet.read_json(path=tmp_path / "search_set.json")
    assert search_set == search_set_copy


def test_searchset_addition() -> None:
    """

    Verify searchset addition.

    :return: Test result or None.
    """
    search_set = SearchSet(searches_list=[FIRST_SEARCH])

    search_set.add(search=SECOND_SEARCH)
    assert len(search_set) == 2
    assert search_set[1] == SECOND_SEARCH
