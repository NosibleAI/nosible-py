import logging
import sqlite3
import os
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
CACHE_DB_PATH = "httpx_cache.sqlite"


class ThreadSafeSyncSqliteStorage(SyncSqliteStorage):
    """
    A subclass of SyncSqliteStorage that:
    1. Disables thread checking (for compatibility with Nosible's concurrency).
    2. Manually defines the full schema (entries + streams) required by Hishel 1.0+.
    """

    def __init__(self, database_path, **kwargs):
        self.db_path = database_path
        super().__init__(database_path=database_path, **kwargs)

    def _ensure_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self.connection.execute("PRAGMA journal_mode=WAL;")

            # 1. Create 'entries' table (Metadata)
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS entries (
                    id BLOB PRIMARY KEY,
                    cache_key TEXT NOT NULL,
                    data BLOB,
                    created_at REAL,
                    deleted_at REAL
                )
                """
            )
            self.connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_key ON entries(cache_key)"
            )

            # 2. Create 'streams' table (Response Body)
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS streams (
                    entry_id BLOB NOT NULL,
                    chunk_number INTEGER NOT NULL,
                    chunk_data BLOB NOT NULL,
                    FOREIGN KEY(entry_id) REFERENCES entries(id)
                )
                """
            )

            self.connection.commit()

        return self.connection


@pytest.fixture(autouse=True, scope="session")
def install_httpx_cache():
    """
    Setup caching for all httpx requests (both sync and async) during tests.
    """
    # Force cleanup of old DB to prevent schema conflicts from previous runs
    if os.path.exists(CACHE_DB_PATH):
        try:
            os.remove(CACHE_DB_PATH)
        except OSError:
            pass

    # Define Shared Policy
    options = CacheOptions(
        allow_stale=True,
        supported_methods=["GET", "POST"]
    )
    policy = SpecificationPolicy(cache_options=options)

    # Setup Synchronous Storage (Use our Custom Class)
    sync_storage = ThreadSafeSyncSqliteStorage(
        database_path=CACHE_DB_PATH,
        default_ttl=60 * 30
    )

    sync_transport = SyncCacheTransport(
        httpx.HTTPTransport(),
        storage=sync_storage,
        policy=policy
    )

    # Setup Asynchronous Storage
    async_storage = AsyncSqliteStorage(
        database_path=CACHE_DB_PATH,
        default_ttl=60 * 30
    )

    async_transport = AsyncCacheTransport(
        httpx.AsyncHTTPTransport(),
        storage=async_storage,
        policy=policy
    )

    # Patch clients
    httpx.Client = partial(httpx.Client, transport=sync_transport, follow_redirects=True)
    httpx.AsyncClient = partial(httpx.AsyncClient, transport=async_transport, follow_redirects=True)

    yield

    # Cleanup
    try:
        sync_storage.close()
    except Exception:
        pass

    if os.path.exists(CACHE_DB_PATH):
        try:
            os.remove(CACHE_DB_PATH)
        except OSError:
            pass


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