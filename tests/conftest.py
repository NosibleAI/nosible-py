import logging
import sqlite3
import os
import threading
import asyncio
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


class NonClosingSyncTransport(httpx.BaseTransport):
    def __init__(self, inner):
        self._inner = inner

    def handle_request(self, request):
        return self._inner.handle_request(request)

    def close(self):
        # Prevent per-client close() from closing the shared cache/DB
        return None


class NonClosingAsyncTransport(httpx.AsyncBaseTransport):
    def __init__(self, inner):
        self._inner = inner

    async def handle_async_request(self, request):
        return await self._inner.handle_async_request(request)

    async def aclose(self):
        # Prevent per-client aclose() from closing the shared cache/DB
        return None


class ThreadSafeSyncSqliteStorage(SyncSqliteStorage):
    """
    A subclass of SyncSqliteStorage that:
    1. Uses a thread lock to prevent race conditions.
    2. Manually defines the schema.
    3. Sets a timeout to handle file locking better.
    """

    def __init__(self, database_path, **kwargs):
        self.db_path = database_path
        self._lock = threading.Lock()
        super().__init__(database_path=database_path, **kwargs)

    def _ensure_connection(self):
        with self._lock:
            if self.connection is None:
                # Added timeout=10 to handle macOS file locking latency
                self.connection = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=10.0
                )
                self.connection.execute("PRAGMA journal_mode=WAL;")

                # 1. Create 'entries' table
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

                # 2. Create 'streams' table
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
    # Cleanup old DB
    if os.path.exists(CACHE_DB_PATH):
        try:
            os.remove(CACHE_DB_PATH)
        except OSError:
            pass

    options = CacheOptions(
        allow_stale=True,
        supported_methods=["GET", "POST"]
    )
    policy = SpecificationPolicy(cache_options=options)

    # Setup Synchronous Storage
    sync_storage = ThreadSafeSyncSqliteStorage(
        database_path=CACHE_DB_PATH,
        default_ttl=60 * 30
    )

    # [CRITICAL FIX] Pre-initialize the DB in the main thread!
    # This creates the tables NOW, so worker threads don't race to do it later.
    sync_storage._ensure_connection()

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
    _real_client = httpx.Client
    _real_async_client = httpx.AsyncClient
    httpx.Client = partial(_real_client, transport=NonClosingSyncTransport(sync_transport), follow_redirects=True)
    httpx.AsyncClient = partial(_real_async_client, transport=NonClosingAsyncTransport(async_transport),
        follow_redirects=True)

    yield

    # Cleanup
    try:
        try:
            sync_transport.close()
        except Exception:
            pass
        try:
            asyncio.run(async_transport.aclose())
        except Exception:
            pass
        sync_storage.close()
    except Exception:
        pass

    # Restore originals (nice hygiene)
    try:
        httpx.Client = _real_client
        httpx.AsyncClient = _real_async_client
    except Exception:
        pass

    if os.path.exists(CACHE_DB_PATH):
        try:
            os.remove(CACHE_DB_PATH)
        except OSError:
            pass


# ... (Rest of your fixtures: search_data, etc. remain exactly the same) ...
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