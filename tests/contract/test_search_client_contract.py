"""HTTP and return-value contracts for all Search API v2.1 endpoints."""

import os
import gzip
import json
import threading
from typing import Any
from unittest.mock import Mock

import httpx
import pytest
import zstandard
from cryptography.fernet import Fernet

import nosible

TEST_MODULE = os.path.basename(p=__file__)


pytestmark = pytest.mark.contract

BATCH_DIRECT_OPTION_CASES = (
    ("expansions", ["shared expansion"], ["model expansion"]),
    (
        "sql_filter",
        "SELECT loc FROM engine WHERE country = 'shared'",
        "SELECT loc FROM engine WHERE country = 'model'"
    ),
    ("n_results", 17, 18),
    ("n_probes", 19, 20),
    ("n_contextify", 256, 320),
    ("algorithm", "hybrid-2", "hybrid-1"),
    ("min_similarity", 0.4, 0.7),
    ("must_include", ["shared required"], ["model required"]),
    ("must_exclude", ["shared excluded"], ["model excluded"]),
    ("brand_safety", "Safe", "Sensitive"),
    ("language", "en", "fr"),
    ("continent", "Africa", "Europe"),
    ("region", "Southern Africa", "Western Europe"),
    ("country", "South Africa", "France"),
    ("sector", "Information Technology", "Industrials"),
    ("industry_group", "Software & Services", "Capital Goods"),
    ("industry", "Software", "Machinery"),
    ("sub_industry", "Application Software", "Industrial Machinery"),
    ("iab_tier_1", "Business and Finance", "Technology & Computing"),
    ("iab_tier_2", "Industries", "Computing"),
    ("iab_tier_3", "Technology Industry", "Computer Software"),
    ("iab_tier_4", "Technology", "Enterprise Software"),
    ("instruction", "Use shared reporting.", "Use model reporting."),
    ("companies", ["Shared Corp"], ["Model Corp"]),
    ("collection", "everything", "this-week"),
    ("deduplicate", True, False),
    ("internal_use", {"scope": "shared"}, {"scope": "model"})
)
LEGACY_OPTION_CASES = (
    ("publish_start", "2025-01-01", "2024-01-01"),
    ("publish_end", "2025-12-31", "2024-12-31"),
    ("visited_start", "2025-02-01", "2024-02-01"),
    ("visited_end", "2025-11-30", "2024-11-30"),
    ("certain", True, False),
    ("include_netlocs", ["shared.example"], ["model.example"]),
    ("exclude_netlocs", ["shared.example"], ["model.example"]),
    ("include_companies", ["shared-company"], ["model-company"]),
    ("exclude_companies", ["shared-company"], ["model-company"]),
    ("include_docs", ["shared-doc"], ["model-doc"]),
    ("exclude_docs", ["shared-doc"], ["model-doc"])
)


class ConcurrentSearchHandler:
    """Record the maximum number of overlapping Fast Search requests."""

    def __init__(
        self: "ConcurrentSearchHandler",
        payload: dict[str, Any],
        required_overlap: int
    ) -> None:
        """
        Initialize the concurrency probe.

        :param payload: Fast Search response payload.
        :param required_overlap: Requests required before releasing waiters.
        :return: None.
        """
        self.payload = payload
        self.required_overlap = required_overlap
        self.lock = threading.Lock()
        self.release = threading.Event()
        self.active = 0
        self.maximum_active = 0

    def __call__(
        self: "ConcurrentSearchHandler",
        request: httpx.Request
    ) -> httpx.Response:
        """
        Block requests until the configured overlap is observed.

        :param request: Fast Search HTTP request.
        :return: Fast Search HTTP response.
        """
        with self.lock:
            self.active += 1
            self.maximum_active = max(self.maximum_active, self.active)
            if self.active >= self.required_overlap:
                self.release.set()
        self.release.wait(timeout=0.2)
        with self.lock:
            self.active -= 1
        return httpx.Response(
            status_code=200,
            json=self.payload,
            request=request
        )


def test_agentic_search_uses_merged_origin_and_returns_result_set(
    client_factory: Any
) -> None:
    """

    Verify agentic search uses merged origin and returns result set.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    results = client.search(
        prompt="Find material changes in semiconductor capacity.",
        agent="cybernaut-1"
    )

    request = recorder.requests[-1]
    assert request.method == "POST"
    assert str(request.url) == "https://nosible.world/api/search/v2/search"
    assert request.headers["api-key"] == "nos_test_contract"
    assert "authorization" not in request.headers
    assert request_json(request=request) == {
        "prompt": "Find material changes in semiconductor capacity.",
        "agent": "cybernaut-1",
    }
    assert isinstance(results, nosible.ResultSet)
    assert results.message == "Search completed."


@pytest.mark.parametrize(
    argnames="kwargs",
    argvalues=[
        {"prompt": "too short"},
        {"prompt": "x" * 2501},
        {
            "prompt": "Find material changes in semiconductor capacity.",
            "agent": "unknown-agent",
        },
    ]
)
def test_agentic_search_openapi_constraints_are_checked_before_io(
    client_factory: Any,
    kwargs: Any
) -> None:
    """

    Verify agentic search openapi constraints are checked before io.

    :param client_factory: Test dependency or input.
    :param kwargs: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    with pytest.raises(expected_exception=ValueError):
        client.search(**kwargs)

    assert recorder.requests == []


def test_fast_search_serializes_every_v2_1_capability(
    client_factory: Any
) -> None:
    """

    Verify fast search serializes every v2 1 capability.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    results = client.fast_search(
        question="semiconductor investment",
        instruction="Retrieve semantically similar text.",
        expansions=["advanced packaging"],
        sql_filter="SELECT loc FROM engine",
        algorithm="hybrid-3",
        min_similarity=0.6,
        must_include=["capacity"],
        must_exclude=["rumour"],
        brand_safety="Safe",
        language="en",
        continent="North America",
        region="North America",
        country="United States",
        sector="Information Technology",
        industry_group="Semiconductors & Semiconductor Equipment",
        industry="Semiconductors & Semiconductor Equipment",
        sub_industry="Semiconductors",
        iab_tier_1="Business and Finance",
        iab_tier_2="Industries",
        iab_tier_3="Technology Industry",
        iab_tier_4="Technology & Computing",
        companies=["NVIDIA", "TSMC"],
        collection="this-week",
        deduplicate=True,
        internal_use={"candidate_strategy": "contract-test"},
        n_results=25,
        n_probes=20,
        n_contextify=512
    )

    request = recorder.requests[-1]
    payload = request_json(request=request)
    assert request.method == "POST"
    assert request.url.path == "/api/search/v2/fast-search"
    assert payload == {
        "question": "semiconductor investment",
        "instruction": "Retrieve semantically similar text.",
        "expansions": ["advanced packaging"],
        "sql_filter": "SELECT loc FROM engine",
        "algorithm": "hybrid-3",
        "min_similarity": 0.6,
        "must_include": ["capacity"],
        "must_exclude": ["rumour"],
        "brand_safety": "Safe",
        "language": "en",
        "continent": "North America",
        "region": "North America",
        "country": "United States",
        "sector": "Information Technology",
        "industry_group": "Semiconductors & Semiconductor Equipment",
        "industry": "Semiconductors & Semiconductor Equipment",
        "sub_industry": "Semiconductors",
        "iab_tier_1": "Business and Finance",
        "iab_tier_2": "Industries",
        "iab_tier_3": "Technology Industry",
        "iab_tier_4": "Technology & Computing",
        "companies": ["NVIDIA", "TSMC"],
        "collection": "this-week",
        "deduplicate": True,
        "internal_use": {"candidate_strategy": "contract-test"},
        "n_results": 25,
        "n_probes": 20,
        "n_contextify": 512,
    }
    assert isinstance(results, nosible.ResultSet)
    assert results[0].similarity == pytest.approx(expected=0.9123)


def test_fast_search_omits_optional_none_values(
    client_factory: Any
) -> None:
    """

    Verify fast search omits optional none values.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    client.fast_search(
        question="semiconductor investment",
        n_results=10
    )

    payload = request_json(request=recorder.requests[-1])
    assert all(value is not None for value in payload.values())
    assert "country" not in payload
    assert "companies" not in payload
    assert "collection" not in payload


def test_fast_searches_keeps_existing_batch_convenience(
    client_factory: Any
) -> None:
    """

    Verify fast searches keeps existing batch convenience.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    result_sets = list(
        client.fast_searches(
            questions=["semiconductor investment", "advanced packaging"],
            n_results=10,
            companies=["NVIDIA"],
            collection="this-week",
            deduplicate=True
        )
    )

    assert len(result_sets) == 2
    assert all(isinstance(item, nosible.ResultSet) for item in result_sets)
    assert [request.url.path for request in recorder.requests] == [
        "/api/search/v2/fast-search",
        "/api/search/v2/fast-search",
    ]
    assert all(
        request_json(request=request)["companies"] == ["NVIDIA"]
        and request_json(request=request)["collection"] == "this-week"
        and request_json(request=request)["deduplicate"] is True
        for request in recorder.requests
    )


def test_fast_searches_honors_configured_concurrency(
    client_factory: Any,
    fast_search_response: Any
) -> None:
    """
    Verify batch searches overlap up to the configured worker count.

    :param client_factory: In-memory NOSIBLE client factory.
    :param fast_search_response: Representative Fast Search response.
    :return: None.
    """
    handler = ConcurrentSearchHandler(
        payload=fast_search_response,
        required_overlap=2
    )
    routes = {
        ("POST", "/api/search/v2/fast-search"): handler
    }
    client, _ = client_factory(
        routes=routes,
        concurrency=2
    )

    results = list(
        client.fast_searches(
            questions=["one", "two", "three"],
            n_results=1
        )
    )

    assert len(results) == 3
    assert handler.maximum_active == 2


def test_fast_searches_forwards_shared_options_to_search_list(
    client_factory: Any
) -> None:
    """
    Verify shared batch options apply to a list of Search models.

    :param client_factory: In-memory NOSIBLE client factory.
    :return: None.
    """
    client, recorder = client_factory()
    searches = [
        nosible.Search(question="semiconductor investment"),
        nosible.Search(question="advanced packaging")
    ]

    result_sets = list(
        client.fast_searches(
            searches=searches,
            n_results=17,
            n_probes=19,
            companies=["NVIDIA"],
            collection="this-week",
            deduplicate=True
        )
    )

    assert len(result_sets) == 2
    for request in recorder.requests:
        payload = request_json(request=request)
        assert payload["n_results"] == 17
        assert payload["n_probes"] == 19
        assert payload["companies"] == ["NVIDIA"]
        assert payload["collection"] == "this-week"
        assert payload["deduplicate"] is True


def test_fast_searches_forwards_shared_options_to_search_set(
    client_factory: Any
) -> None:
    """
    Verify shared batch options apply to a SearchSet.

    :param client_factory: In-memory NOSIBLE client factory.
    :return: None.
    """
    client, recorder = client_factory()
    searches = nosible.SearchSet(
        searches_list=[
            nosible.Search(question="semiconductor investment"),
            nosible.Search(question="advanced packaging")
        ]
    )

    result_sets = list(
        client.fast_searches(
            searches=searches,
            n_results=17,
            n_contextify=256,
            instruction="Prefer direct reporting.",
            internal_use={"batch": "contract"}
        )
    )

    assert len(result_sets) == 2
    for request in recorder.requests:
        payload = request_json(request=request)
        assert payload["n_results"] == 17
        assert payload["n_contextify"] == 256
        assert payload["instruction"] == "Prefer direct reporting."
        assert payload["internal_use"] == {"batch": "contract"}


@pytest.mark.parametrize(
    argnames="container_kind",
    argvalues=["list", "search_set"]
)
@pytest.mark.parametrize(
    argnames="model_overrides",
    argvalues=[False, True]
)
@pytest.mark.parametrize(
    argnames=("option_name", "shared_value", "model_value"),
    argvalues=BATCH_DIRECT_OPTION_CASES
)
def test_fast_searches_applies_every_direct_option_with_model_precedence(
    client_factory: Any,
    container_kind: str,
    model_overrides: bool,
    option_name: str,
    shared_value: Any,
    model_value: Any
) -> None:
    """
    Verify every direct batch option falls back and honors model precedence.

    :param client_factory: In-memory NOSIBLE client factory.
    :param container_kind: Search container representation.
    :param model_overrides: Whether the individual model supplies the option.
    :param option_name: Search option under test.
    :param shared_value: Batch-level option value.
    :param model_value: Individual-model option value.
    :return: None.
    """
    client, recorder = client_factory()
    model_values = {"question": "semiconductor investment"}
    if model_overrides:
        model_values[option_name] = model_value
    search = nosible.Search(**model_values)
    searches = (
        [search]
        if container_kind == "list"
        else nosible.SearchSet(searches_list=[search])
    )

    list(
        client.fast_searches(
            searches=searches,
            **{option_name: shared_value}
        )
    )

    payload = request_json(request=recorder.requests[-1])
    expected_value = model_value if model_overrides else shared_value
    assert payload[option_name] == expected_value


@pytest.mark.parametrize(
    argnames="container_kind",
    argvalues=["list", "search_set"]
)
@pytest.mark.parametrize(
    argnames="model_overrides",
    argvalues=[False, True]
)
@pytest.mark.parametrize(
    argnames=("option_name", "shared_value", "model_value"),
    argvalues=LEGACY_OPTION_CASES
)
def test_fast_searches_applies_every_legacy_filter_with_model_precedence(
    client_factory: Any,
    container_kind: str,
    model_overrides: bool,
    option_name: str,
    shared_value: Any,
    model_value: Any
) -> None:
    """
    Verify every legacy batch filter falls back and honors model precedence.

    :param client_factory: In-memory NOSIBLE client factory.
    :param container_kind: Search container representation.
    :param model_overrides: Whether the individual model supplies the filter.
    :param option_name: Legacy filter under test.
    :param shared_value: Batch-level filter value.
    :param model_value: Individual-model filter value.
    :return: None.
    """
    client, recorder = client_factory()
    model_values = {"question": "semiconductor investment"}
    if model_overrides:
        model_values[option_name] = model_value
    search = nosible.Search(**model_values)
    searches = (
        [search]
        if container_kind == "list"
        else nosible.SearchSet(searches_list=[search])
    )

    list(
        client.fast_searches(
            searches=searches,
            **{option_name: shared_value}
        )
    )

    effective_value = model_value if model_overrides else shared_value
    expected_sql = client.format_sql(**{option_name: effective_value})
    payload = request_json(request=recorder.requests[-1])
    assert payload["sql_filter"] == expected_sql


@pytest.mark.parametrize(
    argnames="container_kind",
    argvalues=["list", "search_set"]
)
@pytest.mark.parametrize(
    argnames=("shared_opt_in", "model_opt_in"),
    argvalues=[
        (True, False),
        (False, True)
    ]
)
def test_fast_searches_generates_expansions_when_either_scope_opts_in(
    client_factory: Any,
    monkeypatch: pytest.MonkeyPatch,
    container_kind: str,
    shared_opt_in: bool,
    model_opt_in: bool
) -> None:
    """
    Verify batch and model expansion-generation flags use opt-in union semantics.

    :param client_factory: In-memory NOSIBLE client factory.
    :param monkeypatch: Active pytest monkeypatch fixture.
    :param container_kind: Search container representation.
    :param shared_opt_in: Batch-level expansion-generation choice.
    :param model_opt_in: Individual-model expansion-generation choice.
    :return: None.
    """
    client, recorder = client_factory()
    generator = Mock(return_value=["generated expansion"])
    monkeypatch.setattr(
        target=client,
        name="generate_expansions",
        value=generator
    )
    search = nosible.Search(
        question="semiconductor investment",
        autogenerate_expansions=model_opt_in
    )
    searches = (
        [search]
        if container_kind == "list"
        else nosible.SearchSet(searches_list=[search])
    )

    list(
        client.fast_searches(
            searches=searches,
            autogenerate_expansions=shared_opt_in
        )
    )

    generator.assert_called_once_with(question="semiconductor investment")
    payload = request_json(request=recorder.requests[-1])
    assert payload["expansions"] == ["generated expansion"]


def test_rich_search_uses_rich_models_and_enrichment_switches(
    client_factory: Any
) -> None:
    """

    Verify rich search uses rich models and enrichment switches.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    results = client.rich_search(
        question="semiconductor investment",
        companies=["NVIDIA"],
        collection="everything",
        deduplicate=True,
        n_results=10,
        enrich_profile=True,
        enrich_targeting=False,
        enrich_history=True,
        enrich_signals=False,
        enrich_vectors=True
    )

    request = recorder.requests[-1]
    payload = request_json(request=request)
    assert request.method == "POST"
    assert request.url.path == "/api/search/v2/rich-search"
    assert payload["companies"] == ["NVIDIA"]
    assert payload["collection"] == "everything"
    assert payload["deduplicate"] is True
    assert payload["enrich_profile"] is True
    assert payload["enrich_targeting"] is False
    assert payload["enrich_history"] is True
    assert payload["enrich_signals"] is False
    assert payload["enrich_vectors"] is True
    assert isinstance(results, nosible.ResultSet)
    assert isinstance(results[0], nosible.RichResult)


@pytest.mark.parametrize(
    argnames=("method_name", "n_results"),
    argvalues=[
        ("fast_search", 0),
        ("fast_search", 101),
        ("rich_search", 9),
        ("rich_search", 101),
    ]
)
def test_interactive_search_result_bounds_are_validated_before_io(
    client_factory: Any,
    method_name: Any,
    n_results: Any
) -> None:
    """

    Verify interactive search result bounds are validated before io.

    :param client_factory: Test dependency or input.
    :param method_name: Test dependency or input.
    :param n_results: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    with pytest.raises(expected_exception=ValueError):
        getattr(client, method_name)(
            question="semiconductor investment",
            n_results=n_results
        )

    assert recorder.requests == []


def test_fast_search_retains_legacy_sub_ten_result_convenience(
    client_factory: Any
) -> None:
    """

    Verify fast search retains legacy sub ten result convenience.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    client.fast_search(
        question="semiconductor investment",
        n_results=5
    )

    assert request_json(request=recorder.requests[-1])["n_results"] == 10


def test_fast_search_clamps_sub_ten_search_model_on_the_wire(
    client_factory: Any
) -> None:
    """

    Verify fast search clamps sub ten search model on the wire.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    client.fast_search(
        search=nosible.Search(
            question="semiconductor investment",
            n_results=5
        )
    )

    assert request_json(request=recorder.requests[-1])["n_results"] == 10


@pytest.mark.parametrize(
    argnames="compression",
    argvalues=["gzip", "zstd"]
)
def test_bulk_search_downloads_decrypts_and_decodes_supported_archives(
    client_factory: Any,
    fast_search_response: Any,
    compression: Any
) -> None:
    """

    Verify bulk search downloads decrypts and decodes supported archives.

    :param client_factory: Test dependency or input.
    :param fast_search_response: Test dependency or input.
    :param compression: Test dependency or input.
    :return: Test result or None.
    """
    key, filename, encrypted = encrypted_download(
                                   fast_search_response=fast_search_response,
                                   compression=compression
                               )
    download_url = f"https://downloads.example/{filename}"
    routes = {
        ("POST", "/api/search/v2/bulk-search"): {
            "json": {
                "message": "Bulk search accepted.",
                "decrypt_using": key,
                "download_from": download_url,
            }
        },
        ("GET", f"/{filename}"): [
            {"status": 404, "json": {"message": "Still running."}},
            {
                "content": encrypted,
                "headers": {"Content-Type": "application/octet-stream"},
            },
        ],
    }
    client, recorder = client_factory(routes=routes)

    results = client.bulk_search(
        question="semiconductor investment",
        companies=["NVIDIA"],
        collection="everything",
        deduplicate=True,
        n_results=1000,
        poll_interval=0,
        poll_timeout=1
    )

    request = recorder.requests[0]
    payload = request_json(request=request)
    assert request.url.path == "/api/search/v2/bulk-search"
    assert payload["companies"] == ["NVIDIA"]
    assert payload["collection"] == "everything"
    assert payload["deduplicate"] is True
    assert [item.url_hash for item in results] == [
        "aB3dE_fG7hIj-KlMnOpQrStU"
    ]
    assert [request.url.path for request in recorder.requests] == [
        "/api/search/v2/bulk-search",
        f"/{filename}",
        f"/{filename}",
    ]
    assert "api-key" not in recorder.requests[1].headers
    assert "authorization" not in recorder.requests[1].headers


def test_bulk_search_polls_unsigned_storage_access_denied(
    client_factory: Any,
    fast_search_response: Any
) -> None:
    """
    Verify transient Wasabi AccessDenied responses remain pollable.

    :param client_factory: Test dependency or input.
    :param fast_search_response: Test dependency or input.
    :return: None.
    """
    key, filename, encrypted = encrypted_download(
        fast_search_response=fast_search_response,
        compression="zstd"
    )
    download_url = f"https://s3.eu-west-1.wasabisys.com/finweb-results/{filename}"
    routes = {
        ("POST", "/api/search/v2/bulk-search"): {
            "json": {
                "message": "Bulk search accepted.",
                "decrypt_using": key,
                "download_from": download_url,
            }
        },
        ("GET", f"/finweb-results/{filename}"): [
            {
                "status": 403,
                "content": b"<Error><Code>AccessDenied</Code></Error>",
                "headers": {"Content-Type": "application/xml"}
            },
            {"content": encrypted}
        ]
    }
    client, recorder = client_factory(routes=routes)

    results = client.bulk_search(
        question="semiconductor investment",
        n_results=1000,
        poll_interval=0,
        poll_timeout=1
    )

    assert len(results) == 1
    assert [request.url.path for request in recorder.requests] == [
        "/api/search/v2/bulk-search",
        f"/finweb-results/{filename}",
        f"/finweb-results/{filename}"
    ]


@pytest.mark.parametrize(
    argnames="n_results",
    argvalues=[999, 10001]
)
def test_bulk_search_bounds_are_validated_before_io(
    client_factory: Any,
    n_results: Any
) -> None:
    """

    Verify bulk search bounds are validated before io.

    :param client_factory: Test dependency or input.
    :param n_results: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    with pytest.raises(expected_exception=ValueError):
        client.bulk_search(
            question="semiconductor investment",
            n_results=n_results
        )

    assert recorder.requests == []


def test_time_search_posts_time_contract_and_decodes_download(
    client_factory: Any,
    fast_search_response: Any
) -> None:
    """

    Verify time search posts time contract and decodes download.

    :param client_factory: Test dependency or input.
    :param fast_search_response: Test dependency or input.
    :return: Test result or None.
    """
    time_result = {
        **fast_search_response["response"][0],
        "published_raw": "2026-07-20T08:30:00+02:00",
        "published_utc": "2026-07-20T06:30:00Z",
        "modified_raw": None,
        "modified_utc": None,
        "visited_raw": "2026-07-20T09:00:00Z",
        "visited_utc": "2026-07-20T09:00:00Z",
        "timezone": "+02:00",
    }
    time_payload = {
        "message": "Completed 1 independent time search.",
        "query": {
            "question": "semiconductor investment",
            "time": {
                "timestamp_field": "published_utc",
                "start": "2026-07-01T00:00:00+00:00",
                "end": "2026-07-20T00:00:00+00:00",
                "sort": "ascending",
                "require_timezone": True,
                "frequency": "1d",
                "results_per_search": 1000,
                "search_count": 1,
            },
        },
        "response": [
            {
                "start": "2026-07-01T00:00:00+00:00",
                "end": "2026-07-02T00:00:00+00:00",
                "result_count": 1,
                "evaluated": 1204213,
                "results": [time_result],
            }
        ],
    }
    key, filename, encrypted = encrypted_download(
                                   fast_search_response=time_payload,
                                   compression="zstd"
                               )
    routes = {
        ("POST", "/api/search/v2/time-search"): {
            "json": {
                "message": "Time search accepted.",
                "decrypt_using": key,
                "download_from": f"https://downloads.example/{filename}",
            }
        },
        ("GET", f"/{filename}"): [
            {"status": 404, "json": {"message": "Still running."}},
            {"content": encrypted},
        ],
    }
    client, recorder = client_factory(routes=routes)

    results = client.time_search(
        start="2026-07-01T00:00:00Z",
        end="2026-07-20T00:00:00Z",
        frequency="1d",
        sort="ascending",
        require_timezone=True,
        n_results=1000,
        n_probes=30,
        n_contextify=256,
        poll_interval=0,
        poll_timeout=1
    )

    payload = request_json(request=recorder.requests[0])
    assert recorder.requests[0].url.path == "/api/search/v2/time-search"
    assert payload == {
        "start": "2026-07-01T00:00:00Z",
        "end": "2026-07-20T00:00:00Z",
        "frequency": "1d",
        "sort": "ascending",
        "require_timezone": True,
        "n_results": 1000,
        "n_probes": 30,
        "n_contextify": 256,
    }
    assert results["query"]["time"]["search_count"] == 1
    assert results["response"][0]["result_count"] == 1
    assert results["response"][0]["results"][0]["url_hash"] == (
        "aB3dE_fG7hIj-KlMnOpQrStU"
    )
    assert results["response"][0]["results"][0]["published_raw"] == (
        "2026-07-20T08:30:00+02:00"
    )
    assert results["response"][0]["results"][0]["timezone"] == "+02:00"
    assert "api-key" not in recorder.requests[1].headers


def encrypted_download(
    fast_search_response: Any,
    *,
    compression: Any
) -> Any:
    """

    Provide encrypted download.

    :param fast_search_response: Test dependency or input.
    :param compression: Test dependency or input.
    :return: Test result or None.
    """
    key = Fernet.generate_key()
    raw = json.dumps(obj=fast_search_response).encode()
    if compression == "gzip":
        compressed = gzip.compress(data=raw)
        filename = "results.gzip.enc"
    else:
        compressed = zstandard.ZstdCompressor().compress(data=raw)
        filename = "results.zstd.enc"
    encrypted = Fernet(key=key).encrypt(data=compressed)
    return key.decode(), filename, encrypted


def test_scrape_url_uses_merged_endpoint_and_existing_model(
    client_factory: Any
) -> None:
    """

    Verify scrape url uses merged endpoint and existing model.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    page = client.scrape_url(
        url="https://example.com",
        html="",
        render=True,
        recrawl=False
    )

    request = recorder.requests[-1]
    assert request.url.path == "/api/search/v2/scrape-url"
    assert request_json(request=request) == {
        "url": "https://example.com",
        "html": "",
        "render": True,
        "recrawl": False,
    }
    assert isinstance(page, nosible.WebPageData)
    assert page.page["title"] == "Example"
    assert page.full_text == "Example page text."
    assert page.languages == {"en": 1.0}
    assert page.metadata == {"description": "Example"}
    assert page.request["raw_url"] == "https://example.com"
    assert page.request["netloc"] == "example.com"
    assert len(page.snippets) == 1
    snippet = page.snippets[0]
    assert snippet.videos == [{"src": "https://example.com/video.mp4"}]
    assert snippet.audio == [{"src": "https://example.com/audio.mp3"}]
    assert snippet.files == [{"href": "https://example.com/report.pdf"}]
    assert snippet.tables == [[["Metric", "Value"], ["Revenue", "42"]]]
    assert snippet.lists == [["first", "second"]]
    assert snippet.blocks == [{"type": "quote", "text": "Example"}]
    assert snippet.to_dict()["future_snippet_field"] == {"kept": True}
    assert page.statistics == {"words": 3}
    assert page.structured == []
    assert page.url_tree == {
        "https://example.com": {
            "about": 1,
            "reports": {"2026": 2},
        }
    }


def test_topic_trend_uses_v2_1_payload(
    client_factory: Any
) -> None:
    """

    Verify topic trend uses v2 1 payload.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    trend = client.topic_trend(
        query="semiconductors",
        sql_filter="SELECT loc FROM engine"
    )

    request = recorder.requests[-1]
    assert request.url.path == "/api/search/v2/topic-trend"
    assert request_json(request=request) == {
        "query": "semiconductors",
        "sql_filter": "SELECT loc FROM engine",
    }
    assert trend["2026-07-20"] == pytest.approx(expected=0.84)


def test_saved_search_lifecycle_uses_all_three_endpoints(
    client_factory: Any
) -> None:
    """

    Verify saved search lifecycle uses all three endpoints.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    saved = client.save_search(
        search_id="saved-1",
        question="semiconductor investment",
        extra_args={"owner": "research"},
        companies=["NVIDIA"],
        collection="this-week",
        deduplicate=True
    )
    searches = client.get_searches()
    deleted = client.delete_search(search_id="saved-1")

    assert [request.url.path for request in recorder.requests] == [
        "/api/search/v2/save-search",
        "/api/search/v2/get-searches",
        "/api/search/v2/delete-search",
    ]
    assert all(request.method == "POST" for request in recorder.requests)
    assert request_json(request=recorder.requests[0])["extra_args"] == {"owner": "research"}
    assert request_json(request=recorder.requests[1]) == {}
    assert request_json(request=recorder.requests[2]) == {"search_id": "saved-1"}
    assert saved["response"]["search_id"] == "saved-1"
    assert searches["response"]["searches"][0]["search_id"] == "saved-1"
    assert deleted["response"]["search_id"] == "saved-1"


def request_json(
    request: Any
) -> Any:
    """

    Provide request json.

    :param request: Test dependency or input.
    :return: Test result or None.
    """
    return json.loads(s=request.content)


@pytest.mark.parametrize(
    argnames=("method_name", "kwargs"),
    argvalues=[
        (
            "rich_search",
            {"question": "semiconductor investment", "n_probes": 51},
        ),
        (
            "bulk_search",
            {"question": "semiconductor investment", "companies": ["a", "b", "c", "d"]},
        ),
        (
            "save_search",
            {"question": "semiconductor investment", "algorithm": "lexical"},
        ),
        ("topic_trend", {"query": "four"}),
        ("delete_search", {"search_id": ""}),
    ]
)
def test_endpoint_specific_inherited_constraints_are_checked_before_io(
    client_factory: Any,
    method_name: Any,
    kwargs: Any
) -> None:
    """

    Verify endpoint specific inherited constraints are checked before io.

    :param client_factory: Test dependency or input.
    :param method_name: Test dependency or input.
    :param kwargs: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    with pytest.raises(expected_exception=ValueError):
        getattr(client, method_name)(**kwargs)

    assert recorder.requests == []


def test_limits_is_explicit_and_does_not_run_during_construction(
    client_factory: Any
) -> None:
    """

    Verify limits is explicit and does not run during construction.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()
    assert recorder.requests == []

    limits = client.get_limits()

    assert recorder.requests[-1].method == "GET"
    assert recorder.requests[-1].url.path == "/api/search/v2/limits"
    assert recorder.requests[-1].headers["api-key"] == "nos_test_contract"
    assert limits["api_key_id"] == "key-1"
    assert limits["limits"][0]["query_type"] == "fast"


def test_search_requires_key_before_making_a_request(
    client_factory: Any
) -> None:
    """

    Verify search requires key before making a request.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory(api_key=None)

    with pytest.raises(expected_exception=nosible.AuthenticationError):
        client.fast_search(question="semiconductor investment")

    assert recorder.requests == []


def test_bulk_search_rejects_malformed_encrypted_download(
    client_factory: Any
) -> None:
    """

    Verify bulk search rejects malformed encrypted download.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    key = Fernet.generate_key().decode()
    filename = "results.zstd.fernet"
    routes = {
        ("POST", "/api/search/v2/bulk-search"): {
            "json": {
                "message": "Bulk search accepted.",
                "decrypt_using": key,
                "download_from": f"https://downloads.example/{filename}",
            }
        },
        ("GET", f"/{filename}"): {"content": b"not-a-fernet-payload"},
    }
    client, recorder = client_factory(routes=routes)

    with pytest.raises(expected_exception=ValueError):
        client.bulk_search(
            question="semiconductor investment",
            n_results=1000,
            poll_interval=0,
            poll_timeout=1
        )

    assert len(recorder.requests) == 2


def test_bulk_search_rejects_unknown_decrypted_compression(
    client_factory: Any
) -> None:
    """

    Verify bulk search rejects unknown decrypted compression.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    key = Fernet.generate_key()
    filename = "results.unknown.fernet"
    routes = {
        ("POST", "/api/search/v2/bulk-search"): {
            "json": {
                "message": "Bulk search accepted.",
                "decrypt_using": key.decode(),
                "download_from": f"https://downloads.example/{filename}",
            }
        },
        ("GET", f"/{filename}"): {
            "content": Fernet(key=key).encrypt(data=b"not-gzip-or-zstandard"),
        },
    }
    client, recorder = client_factory(routes=routes)

    with pytest.raises(
        expected_exception=ValueError,
        match="decode"
    ):
        client.bulk_search(
            question="semiconductor investment",
            n_results=1000,
            poll_interval=0,
            poll_timeout=1
        )

    assert len(recorder.requests) == 2


def test_bulk_search_times_out_when_download_never_appears(
    client_factory: Any
) -> None:
    """

    Verify bulk search times out when download never appears.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    routes = {
        ("POST", "/api/search/v2/bulk-search"): {
            "json": {
                "message": "Bulk search accepted.",
                "decrypt_using": Fernet.generate_key().decode(),
                "download_from": "https://downloads.example/pending.zstd.fernet",
            }
        },
        ("GET", "/pending.zstd.fernet"): pending_download_response
    }
    client, recorder = client_factory(routes=routes)

    with pytest.raises(expected_exception=TimeoutError):
        client.bulk_search(
            question="semiconductor investment",
            n_results=1000,
            poll_interval=0,
            poll_timeout=0
        )

    assert len(recorder.requests) >= 2


def test_custom_base_url_is_normalized_and_never_replaced_by_legacy_origin(
    client_factory: Any
) -> None:
    """

    Verify custom base url is normalized and never replaced by legacy origin.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory(
        base_url="https://staging.example/nosible-api/"
    )

    client.get_limits()

    assert str(recorder.requests[-1].url) == (
        "https://staging.example/nosible-api/search/v2/limits"
    )


@pytest.mark.parametrize(
    argnames="kwargs",
    argvalues=[
        {"question": ""},
        {"question": "x" * 501},
        {"instruction": ""},
        {"instruction": "x" * 501},
        {"expansions": ["x"] * 11},
        {"expansions": ["valid", 1]},
        {"must_include": ["x"] * 101},
        {"must_exclude": ["valid", 1]},
        {"companies": ["one", "two", "three", "four"]},
        {"companies": ["valid", 1]},
        {"collection": "last-month"},
        {"algorithm": "not-an-algorithm"},
        {"brand_safety": "Mostly Safe"},
        {"language": "EN"},
        {"continent": "Atlantis"},
        {"min_similarity": -0.01},
        {"min_similarity": 1.01},
        {"deduplicate": "yes"},
        {"internal_use": []},
        {"n_probes": 4},
        {"n_probes": 51},
        {"n_contextify": 63},
        {"n_contextify": 1025},
        {"n_results": True},
    ]
)
def test_fast_search_openapi_constraints_are_checked_before_io(
    client_factory: Any,
    kwargs: Any
) -> None:
    """

    Verify fast search openapi constraints are checked before io.

    :param client_factory: Test dependency or input.
    :param kwargs: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()
    arguments = {
        "question": "semiconductor investment",
        "n_results": 10,
        **kwargs,
    }

    with pytest.raises(expected_exception=ValueError):
        client.fast_search(**arguments)

    assert recorder.requests == []


@pytest.mark.parametrize(
    argnames="kwargs",
    argvalues=[
        {
            "start": "2026-01-01T00:00:00Z",
            "end": "2027-05-17T00:00:00Z",
            "frequency": "1d",
            "n_results": 1,
        },
        {
            "start": "2026-01-01T00:00:00Z",
            "end": "2026-04-12T00:00:00Z",
            "frequency": "1d",
            "n_results": 500,
        },
    ]
)
def test_time_search_documented_workload_caps_are_checked_before_io(
    client_factory: Any,
    kwargs: Any
) -> None:
    """

    Verify time search documented workload caps are checked before io.

    :param client_factory: Test dependency or input.
    :param kwargs: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    with pytest.raises(expected_exception=ValueError):
        client.time_search(**kwargs)

    assert recorder.requests == []


@pytest.mark.parametrize(
    argnames="kwargs",
    argvalues=[
        {
            "start": "2026-07-01",
            "end": "2026-07-20T00:00:00Z",
        },
        {
            "start": "2026-07-20T00:00:00Z",
            "end": "2026-07-01T00:00:00Z",
        },
        {
            "start": "2026-07-01T00:00:00Z",
            "end": "2026-07-20T00:00:00Z",
            "frequency": "daily",
        },
        {
            "start": "2026-07-01T00:00:00Z",
            "end": "2026-07-20T00:00:00Z",
            "sort": "asc",
        },
        {
            "start": "2026-07-01T00:00:00Z",
            "end": "2026-07-20T00:00:00Z",
            "n_results": 1001,
        },
    ]
)
def test_time_search_openapi_constraints_are_checked_before_io(
    client_factory: Any,
    kwargs: Any
) -> None:
    """

    Verify time search openapi constraints are checked before io.

    :param client_factory: Test dependency or input.
    :param kwargs: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    with pytest.raises(expected_exception=ValueError):
        client.time_search(**kwargs)

    assert recorder.requests == []


def pending_download_response(
    request: httpx.Request
) -> httpx.Response:
    """
    Return the polling response for an unfinished download.

    :param request: Presigned download polling request.
    :return: HTTP not-found response indicating work is still pending.
    """
    return httpx.Response(
        status_code=404,
        json={"message": "Still running."},
        request=request
    )
