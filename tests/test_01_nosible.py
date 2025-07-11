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
        nos.search()
    with pytest.raises(TypeError):
        nos.search(question="foo", search=Search(question="foo"))


def test_search_n_results_limit():
    nos = Nosible(nosible_api_key="test|xyz")
    with pytest.raises(ValueError):
        nos.search(question="foo", n_results=101)


def test_searches_success(searches_data):
    assert len(searches_data) == 2
    for r in searches_data:
        assert isinstance(r, ResultSet)
        assert bool(r)


def test_searches_type_errors():
    nos = Nosible(nosible_api_key="test|xyz")
    with pytest.raises(TypeError):
        nos.searches()
    with pytest.raises(TypeError):
        nos.searches(questions=["A"], searches=SearchSet(searches=["A"]))


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


def test_visit_success_and_error(visit_data):
    assert isinstance(visit_data, WebPageData)
    assert hasattr(visit_data, "languages")
    assert hasattr(visit_data, "page")
    nos = Nosible()
    with pytest.raises(TypeError):
        nos.visit()


def test_version_structure():
    nos = Nosible()
    v = nos.version()
    data = json.loads(v)
    assert isinstance(data, dict)
    assert "response" in data and isinstance(data["response"], dict)
    expected = {"database", "date", "documents", "runtime", "snippets", "time", "tokens", "version", "words"}
    assert set(data["response"].keys()) == expected


def test_indexed_fixture(indexed_data):
    assert indexed_data is True


def test_preflight_output():
    nos = Nosible()
    pf = nos.preflight(url="https://www.dailynewsegypt.com/2023/09/08/g20-and-its-summits/")
    # Turn pf str into a dict
    pf = json.loads(pf)
    assert isinstance(pf, dict)
    assert "response" in pf and isinstance(pf["response"], dict)
    for key in ("domain", "netloc", "raw_url", "scheme", "path", "suffix", "hash"):
        assert key in pf["response"]


def test_get_rate_limits_contains_plans():
    nos = Nosible(nosible_api_key="test|xyz")
    rl = nos.get_rate_limits()
    assert "Free:" in rl and "Basic ($49p/m):" in rl


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


def test_visit_full_attributes(visit_data):
    # all the extra attributes you wanted
    assert isinstance(visit_data.full_text, str)
    assert isinstance(visit_data.languages, dict)
    assert isinstance(visit_data.metadata, dict)
    assert isinstance(visit_data.page, dict)
    assert isinstance(visit_data.request, dict)
    assert isinstance(visit_data.snippets, SnippetSet)
    assert isinstance(visit_data.statistics, dict)
    assert isinstance(visit_data.structured, list)
    assert isinstance(visit_data.url_tree, dict)


def test_visit_save_load(tmp_path, visit_data):
    # save to JSON and reload
    path = tmp_path / "visit_data.json"
    visit_data.save(path)
    loaded = WebPageData.load(path)
    assert isinstance(loaded, WebPageData)
    assert loaded == visit_data
    assert isinstance(loaded.snippets, SnippetSet)


def test_visit_to_json_roundtrip(visit_data):
    # to_json / from_json
    s = visit_data.to_json()
    assert isinstance(s, str)
    rehydrated = WebPageData.from_json(s)
    assert isinstance(rehydrated, WebPageData)
    assert isinstance(rehydrated.snippets, SnippetSet)


def test_trend_success(trend_data):
    # trend_data fixture should give the full payload as a dict
    assert isinstance(trend_data, dict)
    assert trend_data  # non‐empty
    # keys should look like ISO dates, values numeric
    for date_str, count in trend_data.items():
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", date_str)
        assert isinstance(count, (int, float))


def test_trend_date_window(trend_data):
    """
    When start_date/end_date exactly cover the full range,
    trend() should return the same set of dates (keys), regardless of values.
    """
    dates = sorted(trend_data.keys())
    start, end = dates[0], dates[-1]

    with Nosible() as nos:
        windowed = nos.trend(query="any query", start_date=start, end_date=end)
        # Compare only the dates (keys), not the counts
        assert set(windowed.keys()) == set(trend_data.keys())
        # And in the same order if you care about ordering
        assert sorted(windowed.keys()) == dates


def test_trend_invalid_date_format():
    with Nosible() as nos:
        with pytest.raises(ValueError):
            nos.trend(query="q", start_date="20210101")    # Missing hyphens
        with pytest.raises(ValueError):
            nos.trend(query="q", end_date="2021/01/01")    # Wrong separator


def test_search_min_similarity(search_data):
    """
    Using the cached `search_data` as the unfiltered baseline, applying
    min_similarity must never increase the count and must enforce the threshold.
    """
    base_count = len(search_data)
    q = "Hedge funds seek to expand into private credit"

    with Nosible(concurrency=1) as nos:
        filtered = nos.search(question=q, n_results=10, min_similarity=0.9)

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
        inc = nos.search(question=q, n_results=10, must_include=[term])

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
        exc = nos.search(question=q, n_results=10, must_exclude=[term])

    assert len(exc) <= base_count
    # Ensure exclusion really happened
    assert all(term.lower() not in r.content.lower() for r in exc)


def test_answer_raises_if_no_llm_key(search_data):
    nos = Nosible(nosible_api_key="test|xyz", llm_api_key=None)
    nos.llm_api_key = None
    with pytest.raises(ValueError, match="LLM API key"):
        nos.answer("Anything", n_results=1)