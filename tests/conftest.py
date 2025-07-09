import os
import time

import polars as pl
import pytest

from nosible import Nosible, Result, ResultSet, Search, Snippet, SnippetSet
from nosible.classes.search_set import SearchSet
from nosible.classes.web_page import WebPageData

os.environ["NOSIBLE_API_KEY"] = "REDACTED"
os.environ["LLM_API_KEY"] = ""


@pytest.fixture(scope="session")
def search_data():
    """Cache the search results for the session."""
    with Nosible() as nos:
        results = nos.search(question="Hedge funds seek to expand into private credit", n_results=10)
    return results


@pytest.fixture(scope="session")
def snippets_data(visit_data):
    """Cache the snippets data for the session."""
    return visit_data.snippets


@pytest.fixture(scope="session")
def searches_data():
    """Cache a single searches() invocation."""
    queries = SearchSet(
        [
            Search(question="Hedge funds seek to expand into private credit", n_results=5),
            Search(question="How have the Trump tariffs impacted the US economy?", n_results=5),
        ]
    )
    with Nosible() as nos:
        return list(nos.searches(searches=queries))


@pytest.fixture(scope="session")
def visit_data(search_data):
    """Cache one visit() on the second result."""
    with Nosible() as nos:
        return search_data[1].visit(client=nos)


@pytest.fixture(scope="session")
def indexed_data():
    """Cache one indexed() call."""
    with Nosible() as nos:
        return nos.indexed(url="https://www.dailynewsegypt.com/2023/09/08/g20-and-its-summits/")


@pytest.fixture(scope="session")
def bulk_search_data():
    """Cache a single bulk_search() invocation (using a minimal valid size)."""
    with Nosible() as nos:
        # Use n_results=1000 to satisfy the >=1000 requirement
        return nos.bulk_search(question="Hedge funds seek to expand into private credit", n_results=1000)
