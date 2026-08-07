"""Shared fixtures for the offline Search and World contract tests."""

import os
import copy
import json
import re
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any, Iterator, Optional, Union

import httpx
import pytest

import nosible

TEST_MODULE = os.path.basename(p=__file__)


FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_HTTPX_CLIENT = httpx.Client
FAST_SEARCH_RESPONSE = json.loads(
    s=(FIXTURE_DIR / "search_fast_response_v2_1.json").read_text(encoding="utf-8")
)
RICH_SEARCH_RESPONSE = json.loads(
    s=(FIXTURE_DIR / "search_rich_response_v2_1.json").read_text(encoding="utf-8")
)
WORLD_EVENT = json.loads(
    s=(FIXTURE_DIR / "world_event_v1_2.json").read_text(encoding="utf-8")
)


ResponseSpec = Union[
    dict[str, Any],
    Callable[[httpx.Request], httpx.Response]
]


class RequestRecorder:
    """Thread-safe MockTransport handler with endpoint-aware default responses."""

    def __init__(
        self: "RequestRecorder",
        routes: Optional[
            dict[
                tuple[str, str],
                Union[ResponseSpec, list[ResponseSpec]]
            ]
        ] = None
    ) -> None:
        """

        Initialize the test helper.

        :param routes: Test dependency or input.
        :return: Test result or None.
        """
        self.requests: list[httpx.Request] = []
        self.routes = routes or {}
        self.lock = threading.Lock()

    def __call__(
        self: "RequestRecorder",
        request: httpx.Request
    ) -> httpx.Response:
        """

        Invoke the test helper.

        :param request: Test dependency or input.
        :return: Test result or None.
        """
        with self.lock:
            self.requests.append(request)
            route = self.routes.get((request.method, request.url.path))
            if isinstance(route, list):
                route = route.pop(0)

        if callable(route):
            return route(request=request)
        if route is not None:
            return self.response_from_spec(
                       request=request,
                       spec=route
                   )
        return self.default_response(request=request)

    @staticmethod
    def response_from_spec(
        request: httpx.Request,
        spec: dict[str, Any]
    ) -> httpx.Response:
        """

        Provide response from spec.

        :param request: Test dependency or input.
        :param spec: Test dependency or input.
        :return: Test result or None.
        """
        status = spec.get("status", 200)
        headers = spec.get("headers")
        if "content" in spec:
            return httpx.Response(
                status_code=status,
                content=spec["content"],
                headers=headers,
                request=request
            )
        return httpx.Response(
            status_code=status,
            json=copy.deepcopy(x=spec.get("json", {})),
            headers=headers,
            request=request
        )

    @staticmethod
    def default_response(
        request: httpx.Request
    ) -> httpx.Response:
        """

        Provide default response.

        :param request: Test dependency or input.
        :return: Test result or None.
        """
        path = request.url.path

        if path.endswith("/search/v2/limits"):
            payload = {
                "api_key_id": "key-1",
                "subscription_id": "subscription-1",
                "limits": [
                    {
                        "name": "fast_60s",
                        "query_type": "fast",
                        "duration_seconds": 60,
                        "limit": 120,
                    }
                ],
            }
            return httpx.Response(
                status_code=200,
                json=payload,
                request=request
            )
        if path in {
            "/api/search/v2/search",
            "/api/search/v2/fast-search",
        }:
            return httpx.Response(
                status_code=200,
                json=copy.deepcopy(x=FAST_SEARCH_RESPONSE),
                request=request
            )
        if path == "/api/search/v2/rich-search":
            return httpx.Response(
                status_code=200,
                json=copy.deepcopy(x=RICH_SEARCH_RESPONSE),
                request=request
            )
        if path == "/api/search/v2/scrape-url":
            payload = {
                "message": "Page scraped.",
                "added_to_batch": False,
                "response": {
                    "full_text": "Example page text.",
                    "languages": {"en": 1.0},
                    "metadata": {"description": "Example"},
                    "page": {"title": "Example", "url": "https://example.com"},
                    "request": {
                        "domain": None,
                        "fragment": "",
                        "hash": "aB3dE_fG7hIj-KlMnOpQrStU",
                        "netloc": "example.com",
                        "path": "",
                        "query": "",
                        "raw_url": "https://example.com",
                        "scheme": "https",
                        "url": "https://example.com",
                    },
                    "snippets": {
                        "snippet-1": {
                            "url_hash": "aB3dE_fG7hIj-KlMnOpQrStU",
                            "snippet_hash": "snippet-1",
                            "prev_snippet_hash": None,
                            "next_snippet_hash": None,
                            "content": "Example page text.",
                            "words": "example page text",
                            "language": "en",
                            "statistics": {
                                "sentences": 1,
                                "words": 3,
                                "characters": 18,
                            },
                            "images": [{"src": "https://example.com/image.png"}],
                            "videos": [{"src": "https://example.com/video.mp4"}],
                            "audio": [{"src": "https://example.com/audio.mp3"}],
                            "files": [{"href": "https://example.com/report.pdf"}],
                            "tables": [[["Metric", "Value"], ["Revenue", "42"]]],
                            "lists": [["first", "second"]],
                            "blocks": [{"type": "quote", "text": "Example"}],
                            "future_snippet_field": {"kept": True},
                        }
                    },
                    "statistics": {"words": 3},
                    "structured": [],
                    "url_tree": {
                        "https://example.com": {
                            "about": 1,
                            "reports": {"2026": 2},
                        }
                    },
                },
            }
            return httpx.Response(
                status_code=200,
                json=payload,
                request=request
            )
        if path == "/api/search/v2/topic-trend":
            return httpx.Response(
                status_code=200,
                json={
                    "query": {"query": "semiconductors"},
                    "response": {"2026-07-20": 0.84},
                },
                request=request
            )
        if path == "/api/search/v2/save-search":
            return httpx.Response(
                status_code=200,
                json={
                    "message": "Search saved.",
                    "query": {},
                    "response": {"search_id": "saved-1"},
                },
                request=request
            )
        if path == "/api/search/v2/delete-search":
            return httpx.Response(
                status_code=200,
                json={
                    "message": "Search deleted.",
                    "query": {"search_id": "saved-1"},
                    "response": {"search_id": "saved-1"},
                },
                request=request
            )
        if path == "/api/search/v2/get-searches":
            return httpx.Response(
                status_code=200,
                json={
                    "message": "Searches retrieved.",
                    "query": {},
                    "response": {
                        "searches": [
                            {
                                "search_id": "saved-1",
                                "question": "semiconductor investment",
                            }
                        ]
                    },
                },
                request=request
            )

        if path.startswith("/api/markdown/bulk/"):
            return httpx.Response(
                status_code=200,
                content=b"PK\x03\x04contract-zip",
                headers={"Content-Type": "application/zip"},
                request=request
            )
        if path.startswith("/api/markdown/"):
            return httpx.Response(
                status_code=200,
                text="# NOSIBLE World\n\n--- END OF INDEX (lines_emitted=1) ---",
                headers={"Content-Type": "text/markdown; charset=utf-8"},
                request=request
            )

        if (
            re.fullmatch(
                pattern=r"/api/events/\d{4}-\d{2}-\d{2}/[^/]+",
                string=path
            )
            and not path.endswith("/search")
        ):
            return httpx.Response(
                status_code=200,
                json=copy.deepcopy(x=WORLD_EVENT),
                request=request
            )
        if path.endswith("/similar"):
            return httpx.Response(
                status_code=200,
                json={
                    "schema": "nosible_world_similar_events_v1",
                    "event_id": WORLD_EVENT["event_id"],
                    "date": "2026-07-20",
                    "neighbors": [
                        {
                            "event_id": next(iter(WORLD_EVENT["similar"])),
                            "similarity": next(iter(WORLD_EVENT["similar"].values())),
                        }
                    ],
                    "thread": [],
                    "errors": [],
                    "took_ms": 3,
                },
                request=request
            )
        if path.endswith("/aggregates"):
            return httpx.Response(
                status_code=200,
                json={"n_docs": 128, "n_sources": 47},
                request=request
            )
        if path.startswith("/api/coverage/"):
            return httpx.Response(
                status_code=200,
                json={
                    "count": 1,
                    "search_type": "substring",
                    "matched_tokens": ["capacity"],
                    "coverage": [
                        {
                            "doc_hash": "doc-1",
                            "url": "https://wire.example/chip-capacity",
                            "netloc": "wire.example",
                            "snippet": "Capacity is expanding.",
                            "event_score": 0.982,
                            "title": "Chipmakers plan new packaging plants",
                            "published_at": "2026-07-20T08:30:00Z",
                            "language": "en",
                            "country": "United States",
                        }
                    ],
                    "next_cursor": None,
                },
                request=request
            )
        if re.fullmatch(
            pattern=r"/api/search/\d{4}-\d{2}-\d{2}",
            string=path
        ):
            return httpx.Response(
                status_code=200,
                json=[dated_lite_event()],
                request=request
            )
        if path.endswith("/semantic"):
            return httpx.Response(
                status_code=200,
                json={
                    "events": [dated_lite_event()],
                    "count": 1,
                    "query_took_ms": 8,
                    "embedding_ms": 3,
                    "search_ms": 5,
                    "models_used": ["openai/text-embedding-3-large"],
                },
                request=request
            )
        if path == "/api/version":
            return httpx.Response(
                status_code=200,
                json={
                    "build": "contract",
                    "built_at": "2026-07-20T00:00:00Z",
                    "data_epoch": "2026-07-20T12:00:00Z",
                    "archive_cutoff": "2026-07-19",
                    "index_build": "index-1",
                    "global_build_id": "global-1",
                    "live_dates": ["2026-07-20"],
                },
                request=request
            )
        if path == "/api/dates":
            return httpx.Response(
                status_code=200,
                json={"dates": ["2026-07-20", "2026-07-19"]},
                request=request
            )
        if path == "/api/resolve":
            return httpx.Response(
                status_code=200,
                json={
                    "results": [
                        {
                            "type": "ORG",
                            "name": "NVIDIA",
                            "event_count": 48213,
                            "match": "exact",
                        }
                    ]
                },
                request=request
            )
        if path == "/api/entities/summary":
            return httpx.Response(
                status_code=200,
                json={
                    "type": "ORG",
                    "name": "NVIDIA",
                    "total_events": 48213,
                },
                request=request
            )
        if re.fullmatch(
            pattern=r"/api/tickers/[^/]+",
            string=path
        ):
            return httpx.Response(
                status_code=200,
                json={
                    "symbol": "NVDA.US",
                    "name": "NVIDIA Corporation",
                    "total_events": 45102,
                },
                request=request
            )
        if path == "/api/search/schema":
            return httpx.Response(
                status_code=200,
                json={
                    "schema": "nosible_world_search_schema_v1",
                    "revision": 2,
                    "endpoint": "POST /world/v1/search",
                    "search_types": [
                        "metadata",
                        "lexical",
                        "semantic",
                        "hybrid",
                    ],
                    "operators": {},
                    "logical": ["and", "or", "not"],
                    "geo": {},
                    "fields": [],
                },
                request=request
            )
        if path == "/api/snapshots/2026-07-20":
            return httpx.Response(
                status_code=200,
                json={
                    "schema": "nosible_world_snapshot_v1",
                    "date": "2026-07-20",
                    "total": 1,
                    "count": 1,
                    "fields": ["event_id", "title"],
                    "rows": [[WORLD_EVENT["event_id"], WORLD_EVENT["event"]["title"]]],
                },
                request=request
            )

        if re.fullmatch(
            pattern=r"/api/events/\d{4}-\d{2}-\d{2}",
            string=path
        ):
            return httpx.Response(
                status_code=200,
                json=world_page(
                         schema="nosible_world_day_events_v1",
                         event=dated_lite_event()
                     ),
                request=request
            )
        if re.fullmatch(
            pattern=r"/api/events/\d{4}-\d{2}-\d{2}/search",
            string=path
        ):
            return httpx.Response(
                status_code=200,
                json=world_page(
                         schema="nosible_world_day_search_v1",
                         event=dated_lite_event()
                     ),
                request=request
            )
        if path == "/api/entities/events":
            return httpx.Response(
                status_code=200,
                json=world_page(
                         schema="nosible_world_entity_events_v1",
                         entity={
                        "type": "ORG",
                        "name": "NVIDIA",
                        "normalized": "nvidia",
                    },
                         order="desc",
                         date_window={"from": "2026-07-01", "to": "2026-07-20"},
                         live_events=[timeline_lite_event()],
                         hydration_misses=0,
                         as_of={
                        "index_build": "index-1",
                        "archive_cutoff": "2026-07-19",
                    },
                         took_ms=5
                     ),
                request=request
            )
        if re.fullmatch(
            pattern=r"/api/tickers/[^/]+/events",
            string=path
        ):
            return httpx.Response(
                status_code=200,
                json=world_page(
                         schema="nosible_world_ticker_events_v1",
                         event=timeline_lite_event(),
                         ticker={"id_type": "symbol", "value": "NVDA.US"},
                         order="desc",
                         date_window={"from": "2026-07-01", "to": "2026-07-20"},
                         live_events=[],
                         hydration_misses=0,
                         as_of={
                        "index_build": "index-1",
                        "archive_cutoff": "2026-07-19",
                    },
                         took_ms=5
                     ),
                request=request
            )
        if path == "/api/ontology/events":
            return httpx.Response(
                status_code=200,
                json=world_page(
                         schema="nosible_world_ontology_events_v1",
                         classification={
                        "field": "gics_sector",
                        "value": "Information Technology",
                        "match": "top1",
                    },
                         order="desc",
                         date_window={"from": "2026-07-01", "to": "2026-07-20"},
                         hydration_misses=0,
                         as_of={
                        "index_build": "index-1",
                        "archive_cutoff": "2026-07-19",
                    },
                         took_ms=5
                     ),
                request=request
            )
        if path == "/api/search":
            return httpx.Response(
                status_code=200,
                json=world_page(
                         schema="nosible_world_search_response_v1",
                         event=dated_lite_event(),
                         search_type="hybrid",
                         embedding_ms=3,
                         search_ms=5,
                         errors=[]
                     ),
                request=request
            )
        if path == "/api/aggregate":
            return httpx.Response(
                status_code=200,
                json={
                    "schema": "nosible_world_aggregate_v1",
                    "matched_rows": 1,
                    "bucket": "day",
                    "buckets": [
                        {
                            "bucket": "2026-07-20",
                            "count": 1,
                            "sentiment": {
                                "positive": 1,
                                "neutral": 0,
                                "negative": 0,
                            },
                            "materiality": {"high": 1, "medium": 0, "low": 0},
                        }
                    ],
                    "date_window": {
                        "from": "2026-07-01",
                        "to": "2026-07-20",
                        "index_last_date": "2026-07-20",
                        "archive_cutoff": "2026-07-19",
                    },
                    "as_of": {
                        "index_build": "index-1",
                        "archive_cutoff": "2026-07-19",
                    },
                    "co_mentions": {
                        "ORG": [{"name": "TSMC", "count": 1}],
                        "TICKER": [{"name": "TSM.US", "count": 1}],
                        "walked_ordinals": 1,
                    },
                    "took_ms": 2,
                },
                request=request
            )

        raise AssertionError(
            f"No contract fixture for {request.method} {request.url.path}"
        )


class ClientFactory:
    """Create clients backed by endpoint-aware in-memory transports."""

    def __init__(
        self: "ClientFactory",
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Store the active pytest monkeypatch fixture.

        :param monkeypatch: Active pytest monkeypatch fixture.
        :return: None.
        """
        self.monkeypatch = monkeypatch
        self.created: list[tuple[Any, httpx.Client]] = []

    def __call__(
        self: "ClientFactory",
        *,
        api_key: Optional[str] = "nos_test_contract",
        base_url: str = "https://nosible.world/api",
        routes: Optional[
            dict[
                tuple[str, str],
                Union[ResponseSpec, list[ResponseSpec]]
            ]
        ] = None,
        retries: int = 1,
        concurrency: int = 5,
        client_auth: Optional[httpx.Auth] = None,
        client_headers: Optional[dict[str, str]] = None
    ) -> tuple[nosible.Nosible, RequestRecorder]:
        """
        Build a contract client around an in-memory HTTP transport.

        :param api_key: API key supplied to the client.
        :param base_url: Base URL supplied to the client.
        :param routes: Optional endpoint response overrides.
        :param retries: Number of transport retries.
        :param concurrency: Maximum concurrent batch searches.
        :param client_auth: Optional authentication configured on HTTPX.
        :param client_headers: Optional default headers configured on HTTPX.
        :return: Client and request recorder pair.
        """
        self.monkeypatch.delenv(
            name="NOSIBLE_API_KEY",
            raising=False
        )
        recorder = RequestRecorder(routes=routes)
        http_client = REAL_HTTPX_CLIENT(
            transport=httpx.MockTransport(handler=recorder),
            auth=client_auth,
            headers=client_headers
        )

        try:
            client = nosible.Nosible(
                nosible_api_key=api_key,
                base_url=base_url,
                http_client=http_client,
                retries=retries,
                concurrency=concurrency
            )
        except Exception:
            http_client.close()
            raise
        recorder.http_client = http_client
        self.created.append((client, http_client))
        return client, recorder


def timeline_lite_event() -> dict[str, Any]:
    """
    Build the shape emitted by timeline handlers.

    :return: Representative lightweight World event.
    """
    return {
        key: copy.deepcopy(x=WORLD_EVENT[key])
        for key in (
            "event_id",
            "has_tickers",
            "event",
            "coordinate",
            "signals",
            "coverage"
        )
    }


def dated_lite_event() -> dict[str, Any]:
    """
    Build the shape emitted by dated World renderers.

    :return: Representative dated lightweight World event.
    """
    event = {
        key: copy.deepcopy(x=WORLD_EVENT[key])
        for key in (
            "event_id",
            "has_tickers",
            "event",
            "coordinate",
            "signals",
            "coverage",
            "entities",
            "tickers",
            "ontology"
        )
    }
    event["version"] = "1.0"
    return event


def blocked_external_request(
    transport: Any,
    request: httpx.Request
) -> None:
    """
    Reject an accidental external contract-test request.

    :param transport: HTTP transport receiving the request.
    :param request: Outbound HTTP request.
    :return: None.
    """
    raise AssertionError(
        f"Contract tests cannot access the network: {request.url} via {transport!r}"
    )


@pytest.fixture(
    autouse=True,
    scope="session"
)
def install_httpx_cache() -> Iterator[None]:
    """
    Override the legacy live-test cache for deterministic tests.

    :return: Iterator that controls fixture lifetime.
    """
    yield


@pytest.fixture(autouse=True)
def block_external_http(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Install the contract suite's external-request guard.

    :param monkeypatch: Active pytest monkeypatch fixture.
    :return: None.
    """
    monkeypatch.setattr(
        target=httpx.HTTPTransport,
        name="handle_request",
        value=blocked_external_request
    )


@pytest.fixture
def client_factory(
    monkeypatch: pytest.MonkeyPatch
) -> Iterator[ClientFactory]:
    """
    Provide an in-memory NOSIBLE client factory.

    :param monkeypatch: Active pytest monkeypatch fixture.
    :return: Iterator yielding the client factory.
    """
    factory = ClientFactory(monkeypatch=monkeypatch)
    yield factory

    for client, http_client in factory.created:
        try:
            client.close()
        finally:
            if not http_client.is_closed:
                http_client.close()


@pytest.fixture
def fast_search_response() -> dict[str, Any]:
    """
    Provide a fresh Fast Search response payload.

    :return: Fast Search response payload.
    """
    return copy.deepcopy(x=FAST_SEARCH_RESPONSE)


@pytest.fixture
def rich_search_response() -> dict[str, Any]:
    """
    Provide a fresh Rich Search response payload.

    :return: Rich Search response payload.
    """
    return copy.deepcopy(x=RICH_SEARCH_RESPONSE)


@pytest.fixture
def world_event_data() -> dict[str, Any]:
    """
    Provide a fresh World event payload.

    :return: World event payload.
    """
    return copy.deepcopy(x=WORLD_EVENT)


@pytest.fixture
def world_event_page_data() -> dict[str, Any]:
    """
    Provide a fresh World event page payload.

    :return: World event page payload.
    """
    return world_page()


def world_page(
    schema: str = "nosible_world_search_response_v1",
    *,
    event: Optional[dict[str, Any]] = None,
    **metadata: Any
) -> dict[str, Any]:
    """
    Build a representative paginated World response.

    :param schema: Response schema identifier.
    :param event: Optional event payload.
    :param metadata: Response metadata overrides.
    :return: Representative World event page.
    """
    page = {
        "schema": schema,
        "events": [copy.deepcopy(x=event if event is not None else WORLD_EVENT)],
        "total": 1,
        "count": 1,
        "limit": 50,
        "offset": 0,
        "next_cursor": "cursor-next",
        "facets": {},
        "query_took_ms": 4
    }
    page.update(metadata)
    return page
