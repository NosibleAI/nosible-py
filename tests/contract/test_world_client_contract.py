"""HTTP contracts for the complete NOSIBLE World API surface."""

import os
import json
from typing import Any, Iterator

import httpx
import pytest

import nosible

TEST_MODULE = os.path.basename(p=__file__)


pytestmark = pytest.mark.contract

DATE = "2026-07-20"


class InjectedCredentialAuth(httpx.Auth):
    """Authentication policy that exposes accidental client-auth inheritance."""

    def auth_flow(
        self: "InjectedCredentialAuth",
        request: httpx.Request
    ) -> Iterator[httpx.Request]:
        """
        Add representative credentials to an HTTPX request.

        :param request: Outbound HTTPX request.
        :return: Iterator yielding the authenticated request.
        """
        request.headers["Authorization"] = "Bearer injected"
        request.headers["api-key"] = "injected-key"
        yield request


def test_world_day_events_route_and_page_model(
    client_factory: Any
) -> None:
    """

    Verify world day events route and page model.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    page = client.world.events(
               date=DATE,
               limit=50,
               offset=10,
               sort_by="total_netlocs",
               desc=False
           )

    request = recorder.requests[-1]
    assert request.method == "GET"
    assert request.url.path == f"/api/events/{DATE}"
    assert request_params(request=request) == {
        "limit": "50",
        "offset": "10",
        "sort_by": "total_netlocs",
        "desc": "false",
    }
    assert request.headers["authorization"] == "Bearer nos_test_contract"
    assert "api-key" not in request.headers
    assert isinstance(page, nosible.WorldEventPage)
    assert page[0].version == "1.0"


def test_world_entity_timeline_serializes_cursor_window_and_include(
    client_factory: Any
) -> None:
    """

    Verify world entity timeline serializes cursor window and include.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    page = client.world.entity_events(
        entity_type="ORG",
        name="NVIDIA",
        from_="2026-07-01",
        to="2026-07-20",
        limit=20,
        cursor="cursor-1",
        order="desc",
        include="event_full",
        include_vector=True,
        include_live=True
    )

    request = recorder.requests[-1]
    assert request.method == "GET"
    assert request.url.path == "/api/entities/events"
    assert request_params(request=request) == {
        "type": "ORG",
        "name": "NVIDIA",
        "from": "2026-07-01",
        "to": "2026-07-20",
        "limit": "20",
        "cursor": "cursor-1",
        "order": "desc",
        "include": "event_full",
        "include_vector": "true",
        "include_live": "true",
    }
    assert isinstance(page, nosible.WorldEventPage)
    assert len(page.live_events) == 1
    assert page.hydration_misses == 0
    assert page.as_of["index_build"] == "index-1"
    assert page.took_ms == 5


def test_world_ticker_timeline_encodes_symbol_and_identifier_type(
    client_factory: Any,
    world_event_data: Any
) -> None:
    """

    Verify world ticker timeline encodes symbol and identifier type.

    :param client_factory: Test dependency or input.
    :param world_event_data: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    page = client.world.ticker_events(
               symbol="NVDA.US",
               id_type="symbol",
               from_="2026-07-01",
               to="2026-07-20",
               limit=30,
               order="asc",
               include="event_lite",
               include_vector=False,
               include_live=False
           )

    request = recorder.requests[-1]
    assert request.method == "GET"
    assert request.url.path == "/api/tickers/NVDA.US/events"
    assert request_params(request=request) == {
        "id_type": "symbol",
        "from": "2026-07-01",
        "to": "2026-07-20",
        "limit": "30",
        "order": "asc",
        "include": "event_lite",
        "include_vector": "false",
        "include_live": "false",
    }
    assert isinstance(page, nosible.WorldEventPage)
    assert page.live_events == []
    assert page.hydration_misses == 0
    assert page[0].to_dict() == {
        key: world_event_data[key]
        for key in (
            "event_id",
            "has_tickers",
            "event",
            "coordinate",
            "signals",
            "coverage",
        )
    }


def test_world_ontology_timeline_serializes_field_match_and_window(
    client_factory: Any
) -> None:
    """

    Verify world ontology timeline serializes field match and window.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    page = client.world.ontology_events(
        field="gics_sector",
        value="Information Technology",
        match="top1",
        from_="2026-07-01",
        to="2026-07-20",
        limit=15,
        cursor="cursor-2",
        order="desc",
        include="event_full",
        include_vector=True
    )

    request = recorder.requests[-1]
    assert request.method == "GET"
    assert request.url.path == "/api/ontology/events"
    assert request_params(request=request) == {
        "field": "gics_sector",
        "value": "Information Technology",
        "match": "top1",
        "from": "2026-07-01",
        "to": "2026-07-20",
        "limit": "15",
        "cursor": "cursor-2",
        "order": "desc",
        "include": "event_full",
        "include_vector": "true",
    }
    assert isinstance(page, nosible.WorldEventPage)


def test_world_global_search_preserves_filter_dsl(
    client_factory: Any
) -> None:
    """

    Verify world global search preserves filter dsl.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()
    filters = {
        "and": [
            {"sentiment": {"eq": "positive"}},
            {"entity_org": {"contains": "NVIDIA"}},
        ]
    }

    page = client.world.search(
        query="advanced packaging",
        search_type="hybrid",
        date={"from": "2026-07-01", "to": DATE, "include_live": True},
        filters=filters,
        sort=[{"by": "total_coverage", "desc": True}],
        facets=["sentiment", "gics_sector_top3"],
        limit=25,
        offset=5,
        include=["event_lite", "explain"],
        explain=True,
        embedding_model="openai",
        semantic_filter_mode="auto",
        semantic_candidates=500,
        exact_vector_max_candidates=10000,
        max_dates=30
    )

    request = recorder.requests[-1]
    payload = request_json(request=request)
    assert request.method == "POST"
    assert request.url.path == "/api/search"
    assert payload["q"] == "advanced packaging"
    assert payload["search_type"] == "hybrid"
    assert payload["date"]["from"] == "2026-07-01"
    assert payload["filters"] == filters
    assert payload["sort"] == [{"by": "total_coverage", "desc": True}]
    assert payload["facets"] == ["sentiment", "gics_sector_top3"]
    assert payload["include"] == ["event_lite", "explain"]
    assert payload["explain"] is True
    assert payload["semantic_candidates"] == 500
    assert isinstance(page, nosible.WorldEventPage)


def test_world_semantic_search_uses_dated_post_contract(
    client_factory: Any
) -> None:
    """

    Verify world semantic search uses dated post contract.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    page = client.world.semantic_search(
               date=DATE,
               query="advanced semiconductor packaging",
               limit=40,
               embedding_model="openai"
           )

    request = recorder.requests[-1]
    assert request.method == "POST"
    assert request.url.path == f"/api/search/{DATE}/semantic"
    assert request_json(request=request) == {
        "query": "advanced semiconductor packaging",
        "limit": 40,
        "embedding_model": "openai",
    }
    assert isinstance(page, nosible.WorldEventPage)
    assert page.embedding_ms == 3
    assert page.search_ms == 5
    assert page.models_used == ["openai/text-embedding-3-large"]


def test_world_autocomplete_uses_dated_get_contract(
    client_factory: Any
) -> None:
    """

    Verify world autocomplete uses dated get contract.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    page = client.world.autocomplete(
               date=DATE,
               query="chip",
               limit=5
           )

    request = recorder.requests[-1]
    assert request.method == "GET"
    assert request.url.path == f"/api/search/{DATE}"
    assert request_params(request=request) == {"q": "chip", "limit": "5"}
    assert isinstance(page, nosible.WorldEventPage)
    assert len(page) == 1


def test_world_structured_day_search_uses_post_route_from_service_source(
    client_factory: Any
) -> None:
    """

    Verify world structured day search uses post route from service source.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()
    filters = {
        "sentiment": ["positive"],
        "countries": ["United States"],
        "coverage_min": 10,
        "has_tickers": True,
    }

    page = client.world.day_search(
               date=DATE,
               query="capacity",
               filters=filters,
               sort={"by": "total_coverage", "desc": True},
               limit=50,
               offset=0
           )

    request = recorder.requests[-1]
    assert request.method == "POST"
    assert request.url.path == f"/api/events/{DATE}/search"
    assert request_json(request=request) == {
        "q": "capacity",
        "filters": filters,
        "sort": {"by": "total_coverage", "desc": True},
        "limit": 50,
        "offset": 0,
    }
    assert isinstance(page, nosible.WorldEventPage)


def test_world_aggregate_posts_supported_bucket_metrics_and_co_mentions(
    client_factory: Any
) -> None:
    """

    Verify world aggregate posts supported bucket metrics and co mentions.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()
    payload = {
        "date": {"from": "2026-07-01", "to": DATE},
        "filters": {"entity_org": {"contains": "NVIDIA"}},
        "bucket": "day",
        "metrics": ["count", "sentiment", "materiality"],
        "co_mentions": {"types": ["ORG", "TICKER"], "limit": 10},
    }

    response = client.world.aggregate(**payload)

    request = recorder.requests[-1]
    assert request.method == "POST"
    assert request.url.path == "/api/aggregate"
    assert request_json(request=request) == payload
    assert response["schema"] == "nosible_world_aggregate_v1"
    assert response["buckets"][0]["count"] == 1


def request_json(
    request: Any
) -> Any:
    """

    Provide request json.

    :param request: Test dependency or input.
    :return: Test result or None.
    """
    return json.loads(s=request.content)


def test_world_resolve_version_dates_summary_ticker_and_schema(
    client_factory: Any
) -> None:
    """

    Verify world resolve version dates summary ticker and schema.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    resolved = client.world.resolve(
                   query="nvidia",
                   types=["ORG", "TICKER"],
                   limit=10,
                   min_events=5
               )
    version = client.world.version()
    dates = client.world.dates()
    summary = client.world.entity_summary(
        entity_type="ORG",
        name="NVIDIA"
    )
    ticker = client.world.ticker(
                 symbol="NVDA.US",
                 id_type="symbol"
             )
    schema = client.world.search_schema()

    assert [
        (request.method, request.url.path)
        for request in recorder.requests
    ] == [
        ("GET", "/api/resolve"),
        ("GET", "/api/version"),
        ("GET", "/api/dates"),
        ("GET", "/api/entities/summary"),
        ("GET", "/api/tickers/NVDA.US"),
        ("GET", "/api/search/schema"),
    ]
    assert request_params(request=recorder.requests[0]) == {
        "q": "nvidia",
        "types": "ORG,TICKER",
        "limit": "10",
        "min_events": "5",
    }
    assert request_params(request=recorder.requests[3]) == {
        "type": "ORG",
        "name": "NVIDIA",
    }
    assert request_params(request=recorder.requests[4]) == {"id_type": "symbol"}
    assert resolved["results"][0]["name"] == "NVIDIA"
    assert version["global_build_id"] == "global-1"
    assert dates["dates"] == ["2026-07-20", "2026-07-19"]
    assert summary["total_events"] == 48213
    assert ticker["symbol"] == "NVDA.US"
    assert schema["schema"] == "nosible_world_search_schema_v1"
    assert schema["revision"] == 2


def test_world_snapshot_event_similar_aggregates_and_coverage(
    client_factory: Any,
    world_event_data: Any
) -> None:
    """

    Verify world snapshot event similar aggregates and coverage.

    :param client_factory: Test dependency or input.
    :param world_event_data: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()
    event_id = world_event_data["event_id"]

    snapshot = client.world.snapshot(date=DATE)
    event = client.world.event(
                date=DATE,
                event_id=event_id
            )
    similar = client.world.similar_events(
                  date=DATE,
                  event_id=event_id,
                  limit=8,
                  include_live=True,
                  include_thread=False,
                  floor=0.35
              )
    aggregates = client.world.event_aggregates(
                     date=DATE,
                     event_id=event_id
                 )
    coverage = client.world.coverage(
                   date=DATE,
                   event_id=event_id,
                   cursor="coverage-cursor",
                   limit=25,
                   query="capacity"
               )

    assert [
        (request.method, request.url.path)
        for request in recorder.requests
    ] == [
        ("GET", f"/api/snapshots/{DATE}"),
        ("GET", f"/api/events/{DATE}/{event_id}"),
        ("GET", f"/api/events/{DATE}/{event_id}/similar"),
        ("GET", f"/api/events/{DATE}/{event_id}/aggregates"),
        ("GET", f"/api/coverage/{DATE}/{event_id}"),
    ]
    assert request_params(request=recorder.requests[2]) == {
        "limit": "8",
        "include_live": "true",
        "include_thread": "false",
        "floor": "0.35"
    }
    assert request_params(request=recorder.requests[4]) == {
        "cursor": "coverage-cursor",
        "limit": "25",
        "q": "capacity",
    }
    assert snapshot["schema"] == "nosible_world_snapshot_v1"
    assert isinstance(event, nosible.WorldEvent)
    assert event.event_id == event_id
    assert similar["neighbors"][0]["similarity"] == pytest.approx(expected=0.873)
    assert aggregates == {"n_docs": 128, "n_sources": 47}
    assert coverage["coverage"][0]["doc_hash"] == "doc-1"


def test_world_markdown_and_bulk_delivery_routes(
    client_factory: Any,
    world_event_data: Any
) -> None:
    """

    Verify world markdown and bulk delivery routes.

    :param client_factory: Test dependency or input.
    :param world_event_data: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory(
        client_auth=InjectedCredentialAuth(),
        client_headers={
            "Authorization": "Bearer static",
            "api-key": "static-key"
        }
    )
    event_id = world_event_data["event_id"]

    outputs = [
        client.world.markdown_index(
            date=DATE,
            query=["semiconductor", "NVIDIA"],
            top=25
        ),
        client.world.markdown_today(
            query=["earnings", "guidance"],
            top=10
        ),
        client.world.markdown_yesterday(
            query=["tariffs"],
            top=5
        ),
        client.world.markdown_resolve(query="nvidia"),
        client.world.markdown_entity(
            entity_type="ORG",
            name="NVIDIA",
            query=["capacity"],
            top=20
        ),
        client.world.markdown_ticker(
            symbol="NVDA.US",
            query=["earnings"],
            top=15
        ),
        client.world.markdown_event(event_id=event_id),
        client.world.markdown_bulk(date=DATE),
    ]

    assert [
        (request.method, request.url.path)
        for request in recorder.requests
    ] == [
        ("GET", f"/api/markdown/index/{DATE}"),
        ("GET", "/api/markdown/today.md"),
        ("GET", "/api/markdown/yesterday.md"),
        ("GET", "/api/markdown/resolve"),
        ("GET", "/api/markdown/entity"),
        ("GET", "/api/markdown/ticker/NVDA.US"),
        ("GET", f"/api/markdown/event/{event_id}"),
        ("GET", f"/api/markdown/bulk/{DATE}"),
    ]
    assert request_params(request=recorder.requests[0]) == {
        "q": "semiconductor,NVIDIA",
        "top": "25",
    }
    assert request_params(request=recorder.requests[4]) == {
        "type": "ORG",
        "name": "NVIDIA",
        "q": "capacity",
        "top": "20",
    }
    assert all(isinstance(output, str) for output in outputs[:-1])
    assert outputs[-1].startswith(b"PK\x03\x04")
    for request in recorder.requests:
        assert "authorization" not in request.headers
        assert "api-key" not in request.headers


def request_params(
    request: Any
) -> Any:
    """

    Provide request params.

    :param request: Test dependency or input.
    :return: Test result or None.
    """
    return dict(request.url.params.multi_items())


def test_world_programmatic_access_requires_a_key_before_io(
    client_factory: Any
) -> None:
    """

    Verify world programmatic access requires a key before io.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory(api_key=None)

    with pytest.raises(expected_exception=nosible.AuthenticationError):
        client.world.events(
            date=DATE,
            limit=1
        )

    assert recorder.requests == []


def test_world_version_is_public_and_sends_no_credentials(
    client_factory: Any
) -> None:
    """

    Verify world version is public and sends no credentials.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory(api_key=None)

    version = client.world.version()

    assert version["global_build_id"] == "global-1"
    assert len(recorder.requests) == 1
    assert recorder.requests[0].url.path == "/api/version"
    assert "authorization" not in recorder.requests[0].headers
    assert "api-key" not in recorder.requests[0].headers


def test_world_search_schema_is_public_and_sends_no_credentials(
    client_factory: Any
) -> None:
    """

    Verify the public World Search Schema route requires no credentials.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory(
        client_auth=InjectedCredentialAuth(),
        client_headers={
            "Authorization": "Bearer static",
            "api-key": "static-key"
        }
    )

    schema = client.world.search_schema()

    assert schema["schema"] == "nosible_world_search_schema_v1"
    assert len(recorder.requests) == 1
    assert recorder.requests[0].url.path == "/api/search/schema"
    assert "authorization" not in recorder.requests[0].headers
    assert "api-key" not in recorder.requests[0].headers


def test_sdk_authentication_replaces_injected_client_credentials(
    client_factory: Any
) -> None:
    """
    Verify authenticated SDK routes send exactly one endpoint credential.

    :param client_factory: In-memory NOSIBLE client factory.
    :return: None.
    """
    client, recorder = client_factory(
        client_auth=InjectedCredentialAuth(),
        client_headers={
            "Authorization": "Bearer static",
            "api-key": "static-key"
        }
    )

    client.get_limits()
    client.world.dates()

    search_request, world_request = recorder.requests
    assert search_request.headers["api-key"] == "nos_test_contract"
    assert "authorization" not in search_request.headers
    assert world_request.headers["authorization"] == (
        "Bearer nos_test_contract"
    )
    assert "api-key" not in world_request.headers


def test_public_world_routes_retry_with_sdk_bearer_after_authentication_error(
    client_factory: Any
) -> None:
    """
    Verify public World routes adapt to deployments requiring authentication.

    :param client_factory: In-memory NOSIBLE client factory.
    :return: None.
    """
    authentication_error = {
        "status": 401,
        "json": {
            "code": "api_key_required",
            "message": "API key required."
        }
    }
    routes = {
        ("GET", "/api/search/schema"): [
            authentication_error,
            {"json": {"schema": "nosible_world_search_schema_v1"}}
        ],
        ("GET", "/api/markdown/today.md"): [
            authentication_error,
            {"content": b"# Today"}
        ],
        ("GET", f"/api/markdown/bulk/{DATE}"): [
            authentication_error,
            {"content": b"PK\x03\x04archive"}
        ]
    }
    client, recorder = client_factory(
        routes=routes,
        client_auth=InjectedCredentialAuth(),
        client_headers={
            "Authorization": "Bearer static",
            "api-key": "static-key"
        }
    )

    schema = client.world.search_schema()
    markdown = client.world.markdown_today()
    archive = client.world.markdown_bulk(date=DATE)

    assert schema["schema"] == "nosible_world_search_schema_v1"
    assert markdown == "# Today"
    assert archive == b"PK\x03\x04archive"
    assert len(recorder.requests) == 6
    for request_index, request in enumerate(recorder.requests):
        if request_index % 2 == 0:
            assert "authorization" not in request.headers
            assert "api-key" not in request.headers
        else:
            assert request.headers["authorization"] == (
                "Bearer nos_test_contract"
            )
            assert "api-key" not in request.headers


@pytest.mark.parametrize(
    argnames="method_name,args",
    argvalues=[
        ("events", ("20-07-2026",)),
        ("semantic_search", ("20260720", "query")),
        ("event", ("not-a-date", "event-id")),
        ("snapshot", ("yesterday",)),
        ("coverage", ("07/20/2026", "event-id")),
    ]
)
def test_world_date_validation_happens_before_io(
    client_factory: Any,
    method_name: Any,
    args: Any
) -> None:
    """

    Verify world date validation happens before io.

    :param client_factory: Test dependency or input.
    :param method_name: Test dependency or input.
    :param args: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    with pytest.raises(expected_exception=ValueError):
        getattr(client.world, method_name)(*args)

    assert recorder.requests == []


@pytest.mark.parametrize(
    argnames=("method_name", "kwargs"),
    argvalues=[
        (
            "entity_events",
            {"entity_type": "ORG", "name": "NVIDIA", "order": "newest"},
        ),
        (
            "entity_events",
            {"entity_type": "ORG", "name": "NVIDIA", "include": "summary"},
        ),
        ("ticker_events", {"symbol": "NVDA.US", "id_type": "cusip"}),
        (
            "ontology_events",
            {
                "field": "gics_sector_top3",
                "value": "Information Technology",
            },
        ),
        (
            "ontology_events",
            {
                "field": "gics_sector",
                "value": "Information Technology",
                "match": "exact",
            },
        ),
        ("search", {"search_type": "fuzzy"}),
        ("search", {"include": ["raw_document"]}),
        ("aggregate", {"bucket": "quarter"}),
        ("aggregate", {"metrics": ["count", "velocity"]}),
    ]
)
def test_world_enum_contracts_are_checked_before_io(
    client_factory: Any,
    method_name: Any,
    kwargs: Any
) -> None:
    """

    Verify world enum contracts are checked before io.

    :param client_factory: Test dependency or input.
    :param method_name: Test dependency or input.
    :param kwargs: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    with pytest.raises(expected_exception=ValueError):
        getattr(client.world, method_name)(**kwargs)

    assert recorder.requests == []
