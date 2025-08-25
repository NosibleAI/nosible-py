import json
import pytest
import os
import time
import re

import polars as pl

from nosible import Nosible, Result, ResultSet, Search, Snippet, SnippetSet
from nosible.classes.search_set import SearchSet
from nosible.classes.web_page import WebPageData


def test_search_success(search_data):
    assert isinstance(search_data, ResultSet)


def test_search_type_errors():
    nos = Nosible(nosible_api_key="test|xyz")
    with pytest.raises(TypeError):
        nos.fast_search()
    with pytest.raises(TypeError):
        nos.fast_search(question="foo", search=Search(question="foo"))


def test_search_n_results_limit():
    nos = Nosible(nosible_api_key="test|xyz")
    with pytest.raises(ValueError):
        nos.fast_search(question="foo", n_results=101)


def test_searches_success(searches_data):
    assert len(searches_data) == 2
    for r in searches_data:
        assert isinstance(r, ResultSet)
        assert bool(r)


def test_searches_type_errors():
    nos = Nosible(nosible_api_key="test|xyz")
    with pytest.raises(TypeError):
        nos.fast_searches()
    with pytest.raises(TypeError):
        nos.fast_searches(questions=["A"], searches=SearchSet(searches=["A"]))


def test_bulk_search_errors_and_success(bulk_search_data):
    nos = Nosible(nosible_api_key="test|xyz")
    with pytest.raises(ValueError):
        nos.bulk_search(question="x", n_results=100)
    with pytest.raises(TypeError):
        nos.bulk_search()
    with pytest.raises(TypeError):
        nos.bulk_search(question="x", search=Search(question="x"))
    with pytest.raises(ValueError):
        nos.bulk_search(question="x", n_results=10001)

    assert isinstance(bulk_search_data, ResultSet)
    assert len(bulk_search_data) == 1000


def test_scrape_url_success_and_error(scrape_url_data):
    assert isinstance(scrape_url_data, WebPageData)
    assert hasattr(scrape_url_data, "languages")
    assert hasattr(scrape_url_data, "page")
    nos = Nosible()
    with pytest.raises(TypeError):
        nos.scrape_url()


def test_close_idempotent():
    nos = Nosible()
    assert nos.close() is None
    # second close should not raise
    nos.close()


def test_invalid_api_key():
    with pytest.raises(ValueError):
        Nosible(nosible_api_key="test+|xyz")


def test_llm_key_required_for_expansions():
    nos = Nosible(llm_api_key=None)
    nos.llm_api_key = None
    with pytest.raises(ValueError, match="LLM API key is required"):
        nos._generate_expansions("anything")


def test_validate_sql():
    assert Nosible()._validate_sql(sql="SELECT 1")
    assert not Nosible()._validate_sql(sql="SELECT * FROM missing_table")


# —— Your additional tests —— #


def test_search_minimal(search_data):
    # from your snippet: isinstance(search_data, ResultSet)
    assert isinstance(search_data, ResultSet)


def test_scrape_url_full_attributes(scrape_url_data):
    # all the extra attributes you wanted
    assert isinstance(scrape_url_data.full_text, str)
    assert isinstance(scrape_url_data.languages, dict)
    assert isinstance(scrape_url_data.metadata, dict)
    assert isinstance(scrape_url_data.page, dict)
    assert isinstance(scrape_url_data.request, dict)
    assert isinstance(scrape_url_data.snippets, SnippetSet)
    assert isinstance(scrape_url_data.statistics, dict)
    assert isinstance(scrape_url_data.structured, list)
    assert isinstance(scrape_url_data.url_tree, dict)


def test_scrape_url_save_load(tmp_path, scrape_url_data):
    # save to JSON and reload
    path = tmp_path / "scrape_url_data.json"
    scrape_url_data.write_json(path)
    loaded = WebPageData.read_json(path)
    assert isinstance(loaded, WebPageData)
    assert loaded == scrape_url_data
    assert isinstance(loaded.snippets, SnippetSet)


def test_scrape_url_write_json_roundtrip(tmp_path, scrape_url_data):
    # write_json / read_json
    s = scrape_url_data.write_json(tmp_path / "scrape_url_data.json")
    assert isinstance(s, str)
    rehydrated = WebPageData.read_json(tmp_path / "scrape_url_data.json")
    assert isinstance(rehydrated, WebPageData)
    assert isinstance(rehydrated.snippets, SnippetSet)


def test_topic_trend_success(topic_trend_data):
    # topic_trend_data fixture should give the full payload as a dict
    assert isinstance(topic_trend_data, dict)
    assert topic_trend_data  # non‐empty
    # keys should look like ISO dates, values numeric
    for date_str, count in topic_trend_data.items():
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", date_str)
        assert isinstance(count, (int, float))


def test_topic_trend_date_window(topic_trend_data):
    """
    When start_date/end_date exactly cover the full range,
    topic_trend() should return the same set of dates (keys), regardless of values.
    """
    dates = sorted(topic_trend_data.keys())
    start, end = dates[0], dates[-1]

    with Nosible() as nos:
        windowed = nos.topic_trend(query="any query", start_date=start, end_date=end)
        # Compare only the dates (keys), not the counts
        assert set(windowed.keys()) == set(topic_trend_data.keys())
        # And in the same order if you care about ordering
        assert sorted(windowed.keys()) == dates


def test_topic_trend_invalid_date_format():
    with Nosible() as nos:
        with pytest.raises(ValueError):
            nos.topic_trend(query="q", start_date="20210101")    # Missing hyphens
        with pytest.raises(ValueError):
            nos.topic_trend(query="q", end_date="2021/01/01")    # Wrong separator


def test_search_min_similarity(search_data):
    """
    Using the cached `search_data` as the unfiltered baseline, applying
    min_similarity must never increase the count and must enforce the threshold.
    """
    base_count = len(search_data)
    q = "Hedge funds seek to expand into private credit"

    with Nosible(concurrency=1) as nos:
        filtered = nos.fast_search(question=q, n_results=10, min_similarity=0.9)

    assert len(filtered) <= base_count
    assert all(r.similarity >= 0.9 for r in filtered)


def test_search_must_include(search_data):
    """
    must_include should only filter down from the cached `search_data`.
    """
    base_count = len(search_data)
    q = "Hedge funds seek to expand into private credit"
    term = "credit"

    with Nosible(concurrency=1) as nos:
        inc = nos.fast_search(question=q, n_results=10, must_include=[term])

    assert len(inc) <= base_count
    # At least one hit remains
    assert len(inc) > 0


def test_search_must_exclude(search_data):
    """
    must_exclude should only filter out items from the cached `search_data`.
    """
    base_count = len(search_data)
    q = "Hedge funds seek to expand into private credit"
    term = "funds"

    with Nosible(concurrency=1) as nos:
        exc = nos.fast_search(question=q, n_results=10, must_exclude=[term])

    assert len(exc) <= base_count
    # Ensure exclusion really happened
    assert all(term.lower() not in r.content.lower() for r in exc)


def test_answer_raises_if_no_llm_key(search_data):
    nos = Nosible(nosible_api_key="test|xyz", llm_api_key=None)
    nos.llm_api_key = None
    with pytest.raises(ValueError, match="LLM API key"):
        nos.answer("Anything", n_results=1)