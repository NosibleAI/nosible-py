import logging
import os
from datetime import timedelta

import pytest
import requests
import requests_cache

from nosible import Nosible, Search
from nosible.classes.search_set import SearchSet

logging.getLogger("requests_cache").setLevel(logging.DEBUG)


def pytest_addoption(parser):
    parser.addoption("--no-cache", action="store_true", default=False, help="Disable requests_cache entirely")
    parser.addoption(
        "--cache-only", action="store_true", default=False, help="Use only cached responses; don’t hit the network"
    )
    parser.addoption(
        "--clear-cache", action="store_true", default=False, help="Delete the existing HTTP cache before running tests"
    )


@pytest.fixture(autouse=True, scope="session")
def install_requests_cache(request):
    """
    - default (no flags): install cache and update it on misses
    - --no-cache: do nothing (no caching)
    - --cache-only: install cache but only serve cached entries (raise if missing)
    - --clear-cache: delete the cache file before installing (so it will be rebuilt)
    """
    no_cache = request.config.getoption("no_cache")
    cache_only = request.config.getoption("cache_only")
    clear_cache = request.config.getoption("clear_cache")

    if no_cache:
        # skip caching completely
        yield
        return

    cache_name = "http_tests_cache"
    cache_file = f"{cache_name}.sqlite"

    if clear_cache:
        try:
            os.remove(cache_file)
            logging.getLogger("requests_cache").info(f"Removed existing cache file: {cache_file}")
        except FileNotFoundError:
            logging.getLogger("requests_cache").info(f"No cache file to remove: {cache_file}")

    # install the cache (shared session backend)
    requests_cache.install_cache(
        cache_name=cache_name,
        backend="sqlite",
        expire_after=60 * 30,
        allowable_methods=["GET", "POST"],
        # stale_if_error=timedelta(minutes=20)
    )
    logging.getLogger("requests_cache").setLevel(logging.DEBUG)

    if cache_only:
        # monkey-patch Session.request to only_if_cached=True
        orig_request = requests.Session.request

        def only_cached(self, method, url, *args, **kwargs):
            # force only_if_cached; raise if not in cache
            kwargs.setdefault("only_if_cached", True)
            resp = orig_request(self, method, url, *args, **kwargs)
            if getattr(resp, "from_cache", False) is False:
                raise RuntimeError(f"No cached response for {method} {url}")
            return resp

        requests.Session.request = only_cached

    yield


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


@pytest.fixture(scope="session")
def trend_data():
    """Cache a single trend() invocation."""
    with Nosible() as nos:
        return nos.trend(query="Christmas shopping")

