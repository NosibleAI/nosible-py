"""Tests for test 01 nosible."""

import os
import re
from typing import Any

import pytest

from nosible import Nosible, ResultSet, Search, SnippetSet
from nosible.classes.search_set import SearchSet
from nosible.classes.web_page import WebPageData

TEST_MODULE = os.path.basename(p=__file__)


def test_search_success(
    search_data: Any
) -> None:
    """

    Verify search success.

    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    assert isinstance(search_data, ResultSet)


def test_search_type_errors() -> None:
    """

    Verify search type errors.

    :return: Test result or None.
    """
    nos = Nosible(nosible_api_key="test|xyz")
    with pytest.raises(expected_exception=TypeError):
        nos.fast_search()
    with pytest.raises(expected_exception=TypeError):
        nos.fast_search(
            question="foo",
            search=Search(question="foo")
        )


def test_search_n_results_limit() -> None:
    """

    Verify search n results limit.

    :return: Test result or None.
    """
    nos = Nosible(nosible_api_key="test|xyz")
    with pytest.raises(expected_exception=ValueError):
        nos.fast_search(
            question="foo",
            n_results=101
        )


def test_searches_success(
    searches_data: Any
) -> None:
    """

    Verify searches success.

    :param searches_data: Test dependency or input.
    :return: Test result or None.
    """
    assert len(searches_data) == 2
    for result_set in searches_data:
        assert isinstance(result_set, ResultSet)
        assert bool(result_set)


def test_searches_type_errors() -> None:
    """

    Verify searches type errors.

    :return: Test result or None.
    """
    nos = Nosible(nosible_api_key="test|xyz")
    with pytest.raises(expected_exception=TypeError):
        nos.fast_searches()
    with pytest.raises(expected_exception=TypeError):
        nos.fast_searches(
            questions=["A"],
            searches=SearchSet(searches=["A"])
        )


def test_bulk_search_errors_and_success(
    bulk_search_data: Any
) -> None:
    """

    Verify bulk search errors and success.

    :param bulk_search_data: Test dependency or input.
    :return: Test result or None.
    """
    nos = Nosible(nosible_api_key="test|xyz")
    with pytest.raises(expected_exception=ValueError):
        nos.bulk_search(
            question="x",
            n_results=100
        )
    with pytest.raises(expected_exception=TypeError):
        nos.bulk_search()
    with pytest.raises(expected_exception=TypeError):
        nos.bulk_search(
            question="x",
            search=Search(question="x")
        )
    with pytest.raises(expected_exception=ValueError):
        nos.bulk_search(
            question="x",
            n_results=10001
        )

    assert isinstance(bulk_search_data, ResultSet)
    assert len(bulk_search_data) == 1000


def test_scrape_url_success_and_error(
    scrape_url_data: Any
) -> None:
    """

    Verify scrape url success and error.

    :param scrape_url_data: Test dependency or input.
    :return: Test result or None.
    """
    assert isinstance(scrape_url_data, WebPageData)
    assert hasattr(scrape_url_data, "languages")
    assert hasattr(scrape_url_data, "page")
    nos = Nosible()
    with pytest.raises(expected_exception=TypeError):
        nos.scrape_url()


def test_close_idempotent() -> None:
    """

    Verify close idempotent.

    :return: Test result or None.
    """
    nos = Nosible()
    assert nos.close() is None
    nos.close()


def test_llm_key_required_for_expansions() -> None:
    """

    Verify llm key required for expansions.

    :return: Test result or None.
    """
    nos = Nosible(llm_api_key=None)
    nos.llm_api_key = None
    with pytest.raises(
        expected_exception=ValueError,
        match="LLM API key is required"
    ):
        nos.generate_expansions(question="anything")


def test_validate_sql() -> None:
    """

    Verify validate sql.

    :return: Test result or None.
    """
    assert Nosible().validate_sql(sql="SELECT 1")
    assert not Nosible().validate_sql(sql="SELECT * FROM missing_table")


def test_search_minimal(
    search_data: Any
) -> None:
    """

    Verify search minimal.

    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    assert isinstance(search_data, ResultSet)


def test_scrape_url_full_attributes(
    scrape_url_data: Any
) -> None:
    """

    Verify scrape url full attributes.

    :param scrape_url_data: Test dependency or input.
    :return: Test result or None.
    """
    assert isinstance(scrape_url_data.full_text, str)
    assert isinstance(scrape_url_data.languages, dict)
    assert isinstance(scrape_url_data.metadata, dict)
    assert isinstance(scrape_url_data.page, dict)
    assert isinstance(scrape_url_data.request, dict)
    assert isinstance(scrape_url_data.snippets, SnippetSet)
    assert isinstance(scrape_url_data.statistics, dict)
    assert isinstance(scrape_url_data.structured, list)
    assert isinstance(scrape_url_data.url_tree, dict)


def test_scrape_url_save_load(
    tmp_path: Any,
    scrape_url_data: Any
) -> None:
    """

    Verify scrape url save load.

    :param tmp_path: Test dependency or input.
    :param scrape_url_data: Test dependency or input.
    :return: Test result or None.
    """
    path = tmp_path / "scrape_url_data.json"
    scrape_url_data.write_json(path=path)
    loaded = WebPageData.read_json(path=path)
    assert isinstance(loaded, WebPageData)
    assert loaded == scrape_url_data
    assert isinstance(loaded.snippets, SnippetSet)


def test_scrape_url_write_json_roundtrip(
    tmp_path: Any,
    scrape_url_data: Any
) -> None:
    """

    Verify scrape url write json roundtrip.

    :param tmp_path: Test dependency or input.
    :param scrape_url_data: Test dependency or input.
    :return: Test result or None.
    """
    written_path = scrape_url_data.write_json(path=tmp_path / "scrape_url_data.json")
    assert isinstance(written_path, str)
    rehydrated = WebPageData.read_json(path=tmp_path / "scrape_url_data.json")
    assert isinstance(rehydrated, WebPageData)
    assert isinstance(rehydrated.snippets, SnippetSet)


def test_topic_trend_success(
    topic_trend_data: Any
) -> None:
    """

    Verify topic trend success.

    :param topic_trend_data: Test dependency or input.
    :return: Test result or None.
    """
    assert isinstance(topic_trend_data, dict)
    assert topic_trend_data
    for date_str, count in topic_trend_data.items():
        assert re.match(
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            string=date_str
        )
        assert isinstance(count, (int, float))


def test_topic_trend_date_window(
    topic_trend_data: Any
) -> None:
    """
    Verify that an exact date window preserves every result date.

    :param topic_trend_data: Live topic-trend response.
    :return: None.
    """
    dates = sorted(topic_trend_data.keys())
    start, end = dates[0], dates[-1]

    with Nosible() as nos:
        windowed = nos.topic_trend(
            query="any query",
            start_date=start,
            end_date=end
        )
        assert set(windowed.keys()) == set(topic_trend_data.keys())
        assert sorted(windowed.keys()) == dates


def test_topic_trend_invalid_date_format() -> None:
    """

    Verify topic trend invalid date format.

    :return: Test result or None.
    """
    with Nosible() as nos:
        with pytest.raises(expected_exception=ValueError):
            nos.topic_trend(
                query="q",
                start_date="20210101"
            )
        with pytest.raises(expected_exception=ValueError):
            nos.topic_trend(
                query="q",
                end_date="2021/01/01"
            )


def test_search_min_similarity(
    search_data: Any
) -> None:
    """
    Verify that minimum similarity filters the baseline.

    :param search_data: Live unfiltered search results.
    :return: None.
    """
    base_count = len(search_data)
    question = "Hedge funds seek to expand into private credit"

    with Nosible(concurrency=1) as nos:
        filtered = nos.fast_search(
            question=question,
            n_results=10,
            min_similarity=0.9
        )

    assert len(filtered) <= base_count
    assert all(result.similarity >= 0.9 for result in filtered)


def test_search_must_include(
    search_data: Any
) -> None:
    """
    Verify that required terms only reduce the baseline.

    :param search_data: Live unfiltered search results.
    :return: None.
    """
    base_count = len(search_data)
    question = "Hedge funds seek to expand into private credit"
    term = "credit"

    with Nosible(concurrency=1) as nos:
        included_results = nos.fast_search(
            question=question,
            n_results=10,
            must_include=[term]
        )

    assert len(included_results) <= base_count
    assert len(included_results) > 0


def test_search_must_exclude(
    search_data: Any
) -> None:
    """
    Verify that excluded terms do not survive filtering.

    :param search_data: Live unfiltered search results.
    :return: None.
    """
    base_count = len(search_data)
    question = "Hedge funds seek to expand into private credit"
    term = "funds"

    with Nosible(concurrency=1) as nos:
        excluded_results = nos.fast_search(
            question=question,
            n_results=10,
            must_exclude=[term]
        )

    assert len(excluded_results) <= base_count
    assert all(term.lower() not in result.content.lower() for result in excluded_results)


def test_answer_raises_if_no_llm_key(
    search_data: Any
) -> None:
    """

    Verify answer raises if no llm key.

    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    nos = Nosible(
        nosible_api_key="test|xyz",
        llm_api_key=None
    )
    nos.llm_api_key = None
    with pytest.raises(
        expected_exception=ValueError,
        match="LLM API key"
    ):
        nos.answer(
            query="Anything",
            n_results=1
        )
