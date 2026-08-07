"""Synchronous client namespace for every NOSIBLE World endpoint."""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from nosible.classes.world_event import WorldEvent, WorldEventPage
from nosible.exceptions import AuthenticationError
from nosible.transport import NosibleTransport

IDENTIFIER_TYPES = frozenset({"figi", "isin", "lei", "qid", "symbol"})
PROJECTIONS = frozenset({"event_full", "event_lite"})
SEARCH_TYPES = frozenset({"hybrid", "lexical", "metadata", "semantic"})
SEMANTIC_FILTER_MODES = frozenset({"auto", "exact", "usearch"})
SORT_ORDERS = frozenset({"asc", "desc"})


class WorldClient:
    """Provide typed synchronous access to the NOSIBLE World API."""

    def __init__(
        self: "WorldClient",
        transport: NosibleTransport
    ) -> None:
        """
        Initialize the World namespace.

        :param transport: Shared authenticated NOSIBLE transport.
        :return: None.
        """
        self.transport = transport

    def events(
        self: "WorldClient",
        date: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: Optional[str] = None,
        desc: Optional[bool] = None
    ) -> WorldEventPage:
        """
        Return events for one archive date.

        :param date: Archive date in YYYY-MM-DD form.
        :param limit: Maximum number of events.
        :param offset: Zero-based result offset.
        :param sort_by: Optional server-supported sort field.
        :param desc: Whether to sort descending.
        :return: Iterable page of World events.
        """
        validate_date(
            value=date
        )
        data = request_world_json(
            transport=self.transport,
            method="GET",
            path=f"events/{date}",
            params=clean_params(
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                desc=bool_param(
                    value=desc
                ) if desc is not None else None
            )
        )
        return WorldEventPage.from_dict(
            data=data
        )

    def entity_events(
        self: "WorldClient",
        entity_type: str,
        name: str,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        order: str = "desc",
        include: str = "event_lite",
        include_vector: Optional[bool] = None,
        include_live: Optional[bool] = None
    ) -> WorldEventPage:
        """
        Return the event timeline for an entity.

        :param entity_type: Named-entity type or ANY.
        :param name: Canonical entity name.
        :param from_: Optional inclusive first archive date.
        :param to: Optional inclusive last archive date.
        :param limit: Maximum number of events.
        :param cursor: Opaque continuation cursor.
        :param order: Timeline order, asc or desc.
        :param include: Event projection, event_lite or event_full.
        :param include_vector: Whether to include event vectors.
        :param include_live: Whether to include live event slices.
        :return: Iterable cursor page of World events.
        """
        validate_optional_dates(
            from_=from_,
            to=to
        )
        data = request_world_json(
            transport=self.transport,
            method="GET",
            path="entities/events",
            params=clean_params(
                type=entity_type,
                name=name,
                **{
                    "from": from_,
                    "to": to,
                    "limit": limit,
                    "cursor": cursor,
                    "order": validate_order(
                        value=order
                    ),
                    "include": validate_projection(
                        value=include
                    ),
                    "include_vector": optional_bool_param(
                        value=include_vector
                    ),
                    "include_live": optional_bool_param(
                        value=include_live
                    )
                }
            )
        )
        return WorldEventPage.from_dict(
            data=data
        )

    def ticker_events(
        self: "WorldClient",
        symbol: str,
        id_type: str = "symbol",
        from_: Optional[str] = None,
        to: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        order: str = "desc",
        include: str = "event_lite",
        include_vector: Optional[bool] = None,
        include_live: Optional[bool] = None
    ) -> WorldEventPage:
        """
        Return the event timeline for a ticker identifier.

        :param symbol: Ticker symbol or alternate identifier.
        :param id_type: Identifier type.
        :param from_: Optional inclusive first archive date.
        :param to: Optional inclusive last archive date.
        :param limit: Maximum number of events.
        :param cursor: Opaque continuation cursor.
        :param order: Timeline order, asc or desc.
        :param include: Event projection, event_lite or event_full.
        :param include_vector: Whether to include event vectors.
        :param include_live: Whether to include live event slices.
        :return: Iterable cursor page of World events.
        """
        validate_identifier_type(
            value=id_type
        )
        validate_optional_dates(
            from_=from_,
            to=to
        )
        encoded_symbol = quote(
            string=symbol,
            safe=""
        )
        data = request_world_json(
            transport=self.transport,
            method="GET",
            path=f"tickers/{encoded_symbol}/events",
            params=clean_params(
                id_type=id_type,
                **{
                    "from": from_,
                    "to": to,
                    "limit": limit,
                    "cursor": cursor,
                    "order": validate_order(
                        value=order
                    ),
                    "include": validate_projection(
                        value=include
                    ),
                    "include_vector": optional_bool_param(
                        value=include_vector
                    ),
                    "include_live": optional_bool_param(
                        value=include_live
                    )
                }
            )
        )
        return WorldEventPage.from_dict(
            data=data
        )

    def ontology_events(
        self: "WorldClient",
        field: str,
        value: str,
        match: str = "top3",
        from_: Optional[str] = None,
        to: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        order: str = "desc",
        include: str = "event_lite",
        include_vector: Optional[bool] = None
    ) -> WorldEventPage:
        """
        Return the event timeline for an ontology value.

        :param field: World ontology base slot.
        :param value: Ontology value to match.
        :param match: Candidate depth, top1 or top3.
        :param from_: Optional inclusive first archive date.
        :param to: Optional inclusive last archive date.
        :param limit: Maximum number of events.
        :param cursor: Opaque continuation cursor.
        :param order: Timeline order, asc or desc.
        :param include: Event projection, event_lite or event_full.
        :param include_vector: Whether to include event vectors.
        :return: Iterable cursor page of World events.
        """
        validate_ontology_field(
            field=field,
            match=match
        )
        validate_optional_dates(
            from_=from_,
            to=to
        )
        data = request_world_json(
            transport=self.transport,
            method="GET",
            path="ontology/events",
            params=clean_params(
                field=field,
                value=value,
                match=match,
                **{
                    "from": from_,
                    "to": to,
                    "limit": limit,
                    "cursor": cursor,
                    "order": validate_order(
                        value=order
                    ),
                    "include": validate_projection(
                        value=include
                    ),
                    "include_vector": optional_bool_param(
                        value=include_vector
                    )
                }
            )
        )
        return WorldEventPage.from_dict(
            data=data
        )

    def search(
        self: "WorldClient",
        query: Optional[str] = None,
        vector: Optional[List[float]] = None,
        search_type: Optional[str] = None,
        date: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        facets: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include: Optional[List[str]] = None,
        explain: Optional[bool] = None,
        embedding_model: Optional[str] = None,
        semantic_filter_mode: Optional[str] = None,
        semantic_candidates: Optional[int] = None,
        exact_vector_max_candidates: Optional[int] = None,
        max_dates: Optional[int] = None
    ) -> WorldEventPage:
        """
        Search the full World archive.

        :param query: Lexical or semantic query text.
        :param vector: Optional caller-provided query vector.
        :param search_type: Metadata, lexical, semantic, or hybrid mode.
        :param date: Optional date-window object.
        :param filters: World filter DSL.
        :param sort: Ordered sort clauses.
        :param facets: Facet fields to return.
        :param limit: Maximum number of events.
        :param offset: Zero-based result offset.
        :param include: Event projection and explanation selections.
        :param explain: Whether to return scoring explanations.
        :param embedding_model: Embedding model used for semantic retrieval.
        :param semantic_filter_mode: Semantic filtering strategy.
        :param semantic_candidates: Approximate semantic candidate count.
        :param exact_vector_max_candidates: Exact-vector candidate ceiling.
        :param max_dates: Maximum number of archive dates to inspect.
        :return: Iterable World search result page.
        """
        validate_search_options(
            search_type=search_type,
            semantic_filter_mode=semantic_filter_mode,
            include=include,
            date=date
        )
        payload = clean_params(
            q=query,
            vector=vector,
            search_type=search_type,
            date=date,
            filters=filters,
            sort=sort,
            facets=facets,
            limit=limit,
            offset=offset,
            include=include,
            explain=explain,
            embedding_model=embedding_model,
            semantic_filter_mode=semantic_filter_mode,
            semantic_candidates=semantic_candidates,
            exact_vector_max_candidates=exact_vector_max_candidates,
            max_dates=max_dates
        )
        data = request_world_json(
            transport=self.transport,
            method="POST",
            path="search",
            payload=payload
        )
        return WorldEventPage.from_dict(
            data=data
        )

    def aggregate(
        self: "WorldClient",
        filters: Optional[Dict[str, Any]] = None,
        date: Optional[Dict[str, str]] = None,
        bucket: Optional[str] = None,
        metrics: Optional[List[str]] = None,
        co_mentions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Aggregate World events into date buckets and metrics.

        :param filters: World filter DSL.
        :param date: Inclusive aggregation date window.
        :param bucket: Day, week, month, or year bucket.
        :param metrics: Count, sentiment, and materiality metrics.
        :param co_mentions: Co-mention request configuration.
        :return: World aggregate response.
        """
        validate_aggregate_options(
            date=date,
            bucket=bucket,
            metrics=metrics
        )
        return request_world_json(
            transport=self.transport,
            method="POST",
            path="aggregate",
            payload=clean_params(
                filters=filters,
                date=date,
                bucket=bucket,
                metrics=metrics,
                co_mentions=co_mentions
            )
        )

    def resolve(
        self: "WorldClient",
        query: str,
        types: Optional[List[str]] = None,
        limit: Optional[int] = None,
        min_events: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Resolve free text to canonical World entities.

        :param query: Text to resolve.
        :param types: Optional entity types to search.
        :param limit: Maximum number of matches.
        :param min_events: Minimum event-count threshold.
        :return: Entity-resolution response.
        """
        return request_world_json(
            transport=self.transport,
            method="GET",
            path="resolve",
            params=clean_params(
                q=query,
                types=",".join(types) if types is not None else None,
                limit=limit,
                min_events=min_events
            )
        )

    def version(
        self: "WorldClient"
    ) -> Dict[str, Any]:
        """
        Return the public World deployment and data version.

        :return: Public World version response.
        """
        return self.transport.request_json(
            method="GET",
            path="version",
            auth="none"
        )

    def dates(
        self: "WorldClient"
    ) -> Dict[str, Any]:
        """
        Return World archive dates available to the caller.

        :return: Available-date response.
        """
        return request_world_json(
            transport=self.transport,
            method="GET",
            path="dates"
        )

    def entity_summary(
        self: "WorldClient",
        entity_type: str,
        name: str
    ) -> Dict[str, Any]:
        """
        Return the all-time indexed summary for an entity.

        :param entity_type: Named-entity type or ANY.
        :param name: Canonical entity name.
        :return: All-time entity summary.
        """
        return request_world_json(
            transport=self.transport,
            method="GET",
            path="entities/summary",
            params=clean_params(
                type=entity_type,
                name=name
            )
        )

    def ticker(
        self: "WorldClient",
        symbol: str,
        id_type: str = "symbol"
    ) -> Dict[str, Any]:
        """
        Return metadata for a ticker identifier.

        :param symbol: Ticker symbol or alternate identifier.
        :param id_type: Identifier type.
        :return: Ticker metadata response.
        """
        validate_identifier_type(
            value=id_type
        )
        encoded_symbol = quote(
            string=symbol,
            safe=""
        )
        return request_world_json(
            transport=self.transport,
            method="GET",
            path=f"tickers/{encoded_symbol}",
            params={"id_type": id_type}
        )

    def search_schema(
        self: "WorldClient"
    ) -> Dict[str, Any]:
        """
        Return the public World filter and search schema.

        :return: Public World search-schema response.
        """
        return request_public_world_json(
            transport=self.transport,
            path="search/schema"
        )

    def autocomplete(
        self: "WorldClient",
        date: str,
        query: str,
        limit: Optional[int] = None
    ) -> WorldEventPage:
        """
        Return dated autocomplete matches.

        :param date: Archive date in YYYY-MM-DD form.
        :param query: Autocomplete prefix.
        :param limit: Maximum number of matches.
        :return: Iterable autocomplete result page.
        """
        validate_date(
            value=date
        )
        data = request_world_json(
            transport=self.transport,
            method="GET",
            path=f"search/{date}",
            params=clean_params(
                q=query,
                limit=limit
            )
        )
        return WorldEventPage.from_dict(
            data=data
        )

    def semantic_search(
        self: "WorldClient",
        date: str,
        query: str,
        limit: Optional[int] = None,
        embedding_model: Optional[str] = None
    ) -> WorldEventPage:
        """
        Run semantic search against one archive date.

        :param date: Archive date in YYYY-MM-DD form.
        :param query: Semantic query text.
        :param limit: Maximum number of events.
        :param embedding_model: Embedding model identifier.
        :return: Iterable semantic result page.
        """
        validate_date(
            value=date
        )
        data = request_world_json(
            transport=self.transport,
            method="POST",
            path=f"search/{date}/semantic",
            payload=clean_params(
                query=query,
                limit=limit,
                embedding_model=embedding_model
            )
        )
        return WorldEventPage.from_dict(
            data=data
        )

    def day_search(
        self: "WorldClient",
        date: str,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> WorldEventPage:
        """
        Run structured search against one archive date.

        :param date: Archive date in YYYY-MM-DD form.
        :param query: Optional query text.
        :param filters: World filter DSL.
        :param sort: Sort configuration.
        :param limit: Maximum number of events.
        :param offset: Zero-based result offset.
        :return: Iterable dated result page.
        """
        validate_date(
            value=date
        )
        data = request_world_json(
            transport=self.transport,
            method="POST",
            path=f"events/{date}/search",
            payload=clean_params(
                q=query,
                filters=filters,
                sort=sort,
                limit=limit,
                offset=offset
            )
        )
        return WorldEventPage.from_dict(
            data=data
        )

    def snapshot(
        self: "WorldClient",
        date: str
    ) -> Dict[str, Any]:
        """
        Return the compact World snapshot for one date.

        :param date: Archive date in YYYY-MM-DD form.
        :return: Snapshot response.
        """
        validate_date(
            value=date
        )
        return request_world_json(
            transport=self.transport,
            method="GET",
            path=f"snapshots/{date}"
        )

    def event(
        self: "WorldClient",
        date: str,
        event_id: str
    ) -> WorldEvent:
        """
        Return one full World event.

        :param date: Archive date in YYYY-MM-DD form.
        :param event_id: Canonical World event identifier.
        :return: Full World event.
        """
        validate_date(
            value=date
        )
        encoded_event_id = quote(
            string=event_id,
            safe=""
        )
        data = request_world_json(
            transport=self.transport,
            method="GET",
            path=f"events/{date}/{encoded_event_id}"
        )
        return WorldEvent.from_dict(
            data=data
        )

    def similar_events(
        self: "WorldClient",
        date: str,
        event_id: str,
        limit: Optional[int] = None,
        include_live: Optional[bool] = None,
        include_thread: Optional[bool] = None,
        floor: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Return events semantically similar to one World event.

        :param date: Archive date in YYYY-MM-DD form.
        :param event_id: Canonical World event identifier.
        :param limit: Maximum number of neighboring events.
        :param include_live: Whether to include live event slices.
        :param include_thread: Whether to include thread neighbors.
        :param floor: Minimum HNSW neighbor similarity.
        :return: Similar-event response.
        """
        validate_date(
            value=date
        )
        encoded_event_id = quote(
            string=event_id,
            safe=""
        )
        return request_world_json(
            transport=self.transport,
            method="GET",
            path=f"events/{date}/{encoded_event_id}/similar",
            params=clean_params(
                limit=limit,
                include_live=optional_bool_param(
                    value=include_live
                ),
                include_thread=optional_bool_param(
                    value=include_thread
                ),
                floor=floor
            )
        )

    def event_aggregates(
        self: "WorldClient",
        date: str,
        event_id: str
    ) -> Dict[str, Any]:
        """
        Return source and document aggregates for one event.

        :param date: Archive date in YYYY-MM-DD form.
        :param event_id: Canonical World event identifier.
        :return: Event aggregate response.
        """
        validate_date(
            value=date
        )
        encoded_event_id = quote(
            string=event_id,
            safe=""
        )
        return request_world_json(
            transport=self.transport,
            method="GET",
            path=f"events/{date}/{encoded_event_id}/aggregates"
        )

    def coverage(
        self: "WorldClient",
        date: str,
        event_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Return paginated source coverage for one event.

        :param date: Archive date in YYYY-MM-DD form.
        :param event_id: Canonical World event identifier.
        :param cursor: Opaque continuation cursor.
        :param limit: Maximum number of source documents.
        :param query: Optional source-text query.
        :return: Event coverage response.
        """
        validate_date(
            value=date
        )
        encoded_event_id = quote(
            string=event_id,
            safe=""
        )
        return request_world_json(
            transport=self.transport,
            method="GET",
            path=f"coverage/{date}/{encoded_event_id}",
            params=clean_params(
                cursor=cursor,
                limit=limit,
                q=query
            )
        )

    def markdown_index(
        self: "WorldClient",
        date: str,
        query: Optional[List[str]] = None,
        top: Optional[int] = None
    ) -> str:
        """
        Return a dated Markdown event index.

        :param date: Archive date in YYYY-MM-DD form.
        :param query: Optional Markdown filter terms.
        :param top: Maximum number of events.
        :return: Markdown document.
        """
        validate_date(
            value=date
        )
        return request_markdown(
            transport=self.transport,
            path=f"markdown/index/{date}",
            params=markdown_params(
                query=query,
                top=top
            )
        )

    def markdown_today(
        self: "WorldClient",
        query: Optional[List[str]] = None,
        top: Optional[int] = None
    ) -> str:
        """
        Return the current Markdown event index.

        :param query: Optional Markdown filter terms.
        :param top: Maximum number of events.
        :return: Markdown document.
        """
        return request_markdown(
            transport=self.transport,
            path="markdown/today.md",
            params=markdown_params(
                query=query,
                top=top
            )
        )

    def markdown_yesterday(
        self: "WorldClient",
        query: Optional[List[str]] = None,
        top: Optional[int] = None
    ) -> str:
        """
        Return the previous Markdown event index.

        :param query: Optional Markdown filter terms.
        :param top: Maximum number of events.
        :return: Markdown document.
        """
        return request_markdown(
            transport=self.transport,
            path="markdown/yesterday.md",
            params=markdown_params(
                query=query,
                top=top
            )
        )

    def markdown_resolve(
        self: "WorldClient",
        query: str
    ) -> str:
        """
        Return entity resolution as Markdown.

        :param query: Text to resolve.
        :return: Markdown document.
        """
        return request_markdown(
            transport=self.transport,
            path="markdown/resolve",
            params={"q": query}
        )

    def markdown_entity(
        self: "WorldClient",
        entity_type: str,
        name: str,
        query: Optional[List[str]] = None,
        top: Optional[int] = None
    ) -> str:
        """
        Return one entity timeline as Markdown.

        :param entity_type: Named-entity type or ANY.
        :param name: Canonical entity name.
        :param query: Optional Markdown filter terms.
        :param top: Maximum number of events.
        :return: Markdown document.
        """
        return request_markdown(
            transport=self.transport,
            path="markdown/entity",
            params=markdown_params(
                query=query,
                top=top,
                type=entity_type,
                name=name
            )
        )

    def markdown_ticker(
        self: "WorldClient",
        symbol: str,
        query: Optional[List[str]] = None,
        top: Optional[int] = None
    ) -> str:
        """
        Return one ticker timeline as Markdown.

        :param symbol: Canonical ticker symbol.
        :param query: Optional Markdown filter terms.
        :param top: Maximum number of events.
        :return: Markdown document.
        """
        encoded_symbol = quote(
            string=symbol,
            safe=""
        )
        return request_markdown(
            transport=self.transport,
            path=f"markdown/ticker/{encoded_symbol}",
            params=markdown_params(
                query=query,
                top=top
            )
        )

    def markdown_event(
        self: "WorldClient",
        event_id: str
    ) -> str:
        """
        Return one event as Markdown.

        :param event_id: Canonical World event identifier.
        :return: Markdown document.
        """
        encoded_event_id = quote(
            string=event_id,
            safe=""
        )
        return request_markdown(
            transport=self.transport,
            path=f"markdown/event/{encoded_event_id}"
        )

    def markdown_bulk(
        self: "WorldClient",
        date: str
    ) -> bytes:
        """
        Return the dated Markdown bulk ZIP.

        :param date: Archive date in YYYY-MM-DD form.
        :return: ZIP archive bytes.
        """
        validate_date(
            value=date
        )
        return request_public_world_bytes(
            transport=self.transport,
            path=f"markdown/bulk/{date}"
        )


def request_world_json(
    transport: NosibleTransport,
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    payload: Any = None
) -> Any:
    """
    Send an authenticated World JSON request.

    :param transport: Shared NOSIBLE transport.
    :param method: HTTP request method.
    :param path: World API path.
    :param params: Optional query parameters.
    :param payload: Optional JSON request body.
    :return: Parsed JSON response.
    """
    return transport.request_json(
        method=method,
        path=path,
        auth="world",
        params=params,
        json=payload
    )


def request_public_world_json(
    transport: NosibleTransport,
    path: str
) -> Any:
    """
    Send a public World JSON request with a deployment-compatible fallback.

    :param transport: Shared NOSIBLE transport.
    :param path: Public World API path.
    :return: Parsed public World response.
    """
    try:
        return transport.request_json(
            method="GET",
            path=path,
            auth="none"
        )
    except AuthenticationError:
        if not transport.api_key:
            raise
        return transport.request_json(
            method="GET",
            path=path,
            auth="world"
        )


def request_markdown(
    transport: NosibleTransport,
    path: str,
    params: Optional[Dict[str, Any]] = None
) -> str:
    """
    Send a public World Markdown request.

    :param transport: Shared NOSIBLE transport.
    :param path: World Markdown path.
    :param params: Optional query parameters.
    :return: Public Markdown response text.
    """
    try:
        return transport.request(
            method="GET",
            path=path,
            auth="none",
            params=params
        ).text
    except AuthenticationError:
        if not transport.api_key:
            raise
        return transport.request(
            method="GET",
            path=path,
            auth="world",
            params=params
        ).text


def request_public_world_bytes(
    transport: NosibleTransport,
    path: str
) -> bytes:
    """
    Send a public World binary request with an authenticated fallback.

    :param transport: Shared NOSIBLE transport.
    :param path: Public World binary path.
    :return: Public World response bytes.
    """
    try:
        return transport.request(
            method="GET",
            path=path,
            auth="none"
        ).content
    except AuthenticationError:
        if not transport.api_key:
            raise
        return transport.request(
            method="GET",
            path=path,
            auth="world"
        ).content


def markdown_params(
    query: Optional[List[str]],
    top: Optional[int],
    **values: Any
) -> Dict[str, Any]:
    """
    Build common Markdown query parameters.

    :param query: Optional Markdown filter terms.
    :param top: Maximum number of events.
    :param values: Additional Markdown query parameters.
    :return: Query parameters without null values.
    """
    return clean_params(
        **values,
        q=",".join(query) if query is not None else None,
        top=top
    )


def validate_search_options(
    search_type: Optional[str],
    semantic_filter_mode: Optional[str],
    include: Optional[List[str]],
    date: Optional[Dict[str, Any]]
) -> None:
    """
    Validate global World search options before network I/O.

    :param search_type: Requested global search mode.
    :param semantic_filter_mode: Requested semantic filter strategy.
    :param include: Requested response projections.
    :param date: Optional date-window object.
    :return: None.
    """
    if search_type is not None and search_type not in SEARCH_TYPES:
        raise ValueError("invalid search_type")
    if semantic_filter_mode is not None and semantic_filter_mode not in SEMANTIC_FILTER_MODES:
        raise ValueError("invalid semantic_filter_mode")
    if include is not None:
        invalid = set(include) - {"event_lite", "event_full", "explain"}
        if invalid:
            raise ValueError(f"unsupported include values: {sorted(invalid)}")
    if date is not None:
        validate_optional_dates(
            from_=date.get("from"),
            to=date.get("to")
        )


def validate_aggregate_options(
    date: Optional[Dict[str, str]],
    bucket: Optional[str],
    metrics: Optional[List[str]]
) -> None:
    """
    Validate World aggregation options before network I/O.

    :param date: Optional aggregation date window.
    :param bucket: Requested aggregation bucket.
    :param metrics: Requested aggregation metrics.
    :return: None.
    """
    if date is not None:
        validate_optional_dates(
            from_=date.get("from"),
            to=date.get("to")
        )
    if bucket is not None and bucket not in {"day", "week", "month", "year"}:
        raise ValueError("bucket must be day, week, month, or year")
    if metrics is not None:
        invalid = set(metrics) - {"count", "sentiment", "materiality"}
        if invalid:
            raise ValueError(f"unsupported aggregate metrics: {sorted(invalid)}")


def validate_ontology_field(
    field: str,
    match: str
) -> None:
    """
    Validate an ontology timeline selector.

    :param field: World ontology base slot.
    :param match: Candidate depth, top1 or top3.
    :return: None.
    """
    if not field or "." in field or field.endswith("_top3"):
        raise ValueError("field must be a World ontology base slot")
    if match not in {"top1", "top3"}:
        raise ValueError("match must be 'top1' or 'top3'")


def validate_optional_dates(
    from_: Optional[str],
    to: Optional[str]
) -> None:
    """
    Validate optional inclusive World date bounds.

    :param from_: Optional first archive date.
    :param to: Optional last archive date.
    :return: None.
    """
    if from_ is not None:
        validate_date(
            value=from_,
            name="from_"
        )
    if to is not None:
        validate_date(
            value=to,
            name="to"
        )


def validate_date(
    value: str,
    name: str = "date"
) -> str:
    """
    Validate a strict World archive date.

    :param value: Date text to validate.
    :param name: Parameter name used in validation errors.
    :return: Validated YYYY-MM-DD value.
    """
    if not isinstance(value, str):
        raise ValueError(f"{name} must use YYYY-MM-DD")
    value = os.fspath(path=value)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must use YYYY-MM-DD") from exc
    if parsed.strftime(format="%Y-%m-%d") != value:
        raise ValueError(f"{name} must use YYYY-MM-DD")
    return value


def validate_identifier_type(
    value: str
) -> str:
    """
    Validate a World ticker identifier type.

    :param value: Identifier type to validate.
    :return: Validated identifier type.
    """
    if value not in IDENTIFIER_TYPES:
        raise ValueError("id_type must be symbol, isin, figi, lei, or qid")
    return value


def validate_projection(
    value: str
) -> str:
    """
    Validate a World event projection.

    :param value: Projection to validate.
    :return: Validated projection.
    """
    if value not in PROJECTIONS:
        raise ValueError("include must be 'event_lite' or 'event_full'")
    return value


def validate_order(
    value: str
) -> str:
    """
    Validate a World timeline order.

    :param value: Timeline order to validate.
    :return: Validated timeline order.
    """
    if value not in SORT_ORDERS:
        raise ValueError("order must be 'asc' or 'desc'")
    return value


def optional_bool_param(
    value: Optional[bool]
) -> Optional[str]:
    """
    Serialize an optional Boolean query parameter.

    :param value: Optional Boolean value.
    :return: Lowercase Boolean text or None.
    """
    return bool_param(
        value=value
    ) if value is not None else None


def bool_param(
    value: bool
) -> str:
    """
    Serialize a Boolean query parameter.

    :param value: Boolean value.
    :return: Lowercase Boolean text.
    """
    return "true" if value else "false"


def clean_params(
    **values: Any
) -> Dict[str, Any]:
    """
    Remove null values from request parameters.

    :param values: Candidate request parameters.
    :return: Request parameters without null values.
    """
    return {
        key: value
        for key, value in values.items()
        if value is not None
    }
