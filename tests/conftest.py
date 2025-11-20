import logging
from functools import partial

import httpx
import pytest
from hishel import (
    CacheOptions,
    SpecificationPolicy,
    SyncSqliteStorage,
    AsyncSqliteStorage
)
from hishel.httpx import SyncCacheTransport, AsyncCacheTransport

from nosible import Nosible, Search
from nosible.classes.search_set import SearchSet

logging.getLogger("requests_cache").setLevel(logging.DEBUG)

CACHE_DIR = "httpx_tests_cache"

# Define a file name for the DB instead of a directory
CACHE_DB_PATH = "httpx_cache.sqlite"


@pytest.fixture(autouse=True, scope="session")
def install_httpx_cache():
    """
    Setup caching for all httpx requests (both sync and async) during tests.
    """
    # 1. Define Shared Policy
    options = CacheOptions(
        always_cache=True,
        supported_methods=["GET", "POST"]
    )
    policy = SpecificationPolicy(cache_options=options)

    # 2. Setup Synchronous Storage (SQLite)
    # Use 'database_path' and 'default_ttl'
    sync_storage = SyncSqliteStorage(
        database_path=CACHE_DB_PATH,
        default_ttl=60 * 30
    )
    sync_transport = SyncCacheTransport(
        transport=httpx.HTTPTransport(),
        storage=sync_storage,
        policy=policy
    )

    # 3. Setup Asynchronous Storage (SQLite)
    # Point to the same DB file
    async_storage = AsyncSqliteStorage(
        database_path=CACHE_DB_PATH,
        default_ttl=60 * 30
    )
    async_transport = AsyncCacheTransport(
        transport=httpx.AsyncHTTPTransport(),
        storage=async_storage,
        policy=policy
    )

    # 4. Patch clients
    httpx.Client = partial(httpx.Client, transport=sync_transport, follow_redirects=True)
    httpx.AsyncClient = partial(httpx.AsyncClient, transport=async_transport, follow_redirects=True)

    yield

    # Optional: You might want to close the storage connections explicitly if tests hang,
    # but usually the fixture teardown handles this fine for sessions.
    sync_storage.close()
    # Async close is trickier in a sync fixture, but typically acceptable to skip for simple test caches.


@pytest.fixture(scope="session")
def search_data():
    """Cache the search results for the session."""
    with Nosible() as nos:
        results = nos.fast_search(question="Hedge funds seek to expand into private credit", n_results=10)
    return results


@pytest.fixture(scope="session")
def snippets_data(scrape_url_data):
    """Cache the snippets data for the session."""
    return scrape_url_data.snippets


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
        return list(nos.fast_searches(searches=queries))


@pytest.fixture(scope="session")
def scrape_url_data(search_data):
    """Cache one scrape_url() on the second result."""
    with Nosible() as nos:
        return search_data[1].scrape_url(client=nos)


@pytest.fixture(scope="session")
def bulk_search_data():
    """Cache a single bulk_search() invocation (using a minimal valid size)."""
    with Nosible() as nos:
        # Use n_results=1000 to satisfy the >=1000 requirement
        return nos.bulk_search(question="Hedge funds seek to expand into private credit", n_results=1000)


@pytest.fixture(scope="session")
def topic_trend_data():
    """Cache a single topic_trend() invocation."""
    with Nosible() as nos:
        return nos.topic_trend(query="Christmas shopping")
