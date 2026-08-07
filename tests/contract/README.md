# Search + World SDK contract

These offline tests define and verify the public contract for `0.4.0`. They
were written before the implementation and remain the release regression
suite; they must not be marked `xfail`.

## Sources

- Search API v2.1 OpenAPI:
  <https://docs.nosible.com/openapi/search-v2.json>
- Current combined API reference:
  <https://docs.nosible.com/>
- NOSIBLE World v1.2 data dictionary:
  <https://nosible.com/files/data-dictionaries/NOSIBLE-World-V1.2-Data-Dictionary.pdf>
- Published data-dictionary index:
  <https://nosible.com/data-dictionaries>
- Representative World v1.2 event:
  <https://nosible.com/start-trial>
- Canonical local World event projector:
  `../../monorepo/world-engine/package/src/nosible_world/pipeline/stages/s19_emit.py`
- Current World BFF routes:
  `../../monorepo/railway-web/nosible-world/app/api`

The generated `llms-full.txt` endpoint inventory currently labels
`/api/events/{date}/search` as GET. The checked-in World route, its API page,
its frontend client, and its route comment all implement POST, so the contract
uses POST.

The deployed `/api/version`, `/api/search/schema`, and Markdown delivery routes
have a public contract. Version is always credential-free. Search Schema and
Markdown delivery use a public-first request and may retry once with
SDK-managed bearer authentication when a deployment rejects anonymous access.
Other World routes require bearer authentication.

`/api/dates` is an unfiltered archive directory. The Similar Events contract
includes the optional caller-supplied `floor` query parameter.

## Public design frozen by the tests

- `Nosible` remains the facade and existing 0.3 symbols stay public.
- The constructor accepts `base_url` and an injected `httpx.Client`, and does
  not perform an eager limits request.
- Search endpoints live below `/api/search/v2/*` and send `Api-Key`.
- `client.world` owns the World namespace and sends
  `Authorization: Bearer <key>` when a key is present.
- Search and authenticated World calls require an API key. World version,
  Search Schema, and Markdown delivery routes have a public contract. Version
  never sends credentials; Schema and Markdown retry once with SDK-managed
  bearer authentication only after an authentication error and only when a
  key is configured.
- `Search` gains `companies`, `collection`, and `deduplicate`.
- Fast responses remain `Result`/`ResultSet` compatible. The documented
  top-level `best_chunk` and `content` fields remain available, while
  `semantics.similarity` populates the legacy similarity property.
- Rich Search returns `RichResult` instances without flattening or losing any
  enrichment block.
- Scrape snippets retain all documented media/content blocks and unknown
  future fields, while sparse payloads preserve omitted fields and explicit
  nulls exactly.
- `WorldEvent` mirrors the v1.2 event payload and round-trips unknown NER,
  ontology, and top-level fields.
- `WorldEventPage` gives event-returning endpoints one consistent iterable,
  indexable result while retaining offset, cursor, facet, and timing metadata.
- HTTP failures use a typed, backwards-compatible `ValueError` hierarchy with
  status, error code, method, path, body, and retry metadata.
- Bulk and Time Search poll 404-to-ready downloads, never forward API
  credentials to object storage, and accept both legacy gzip and current
  Zstandard encrypted payloads. Bulk remains a `ResultSet`; Time preserves
  interval buckets.
- Presigned downloads retry transient HTTP statuses without turning a pending
  404 into a transport retry.
- `fast_searches` forwards shared options to question batches,
  `list[Search]`, and `SearchSet` inputs. Non-null model values override shared
  values, while expansion generation is enabled when either scope opts in.
  Requests are concurrent up to the configured limit and results retain input
  order.

## Endpoint coverage

The suite exercises all 11 Search endpoints:

1. limits
2. agentic search
3. fast search
4. time search
5. rich search
6. bulk search
7. scrape URL
8. topic trend
9. save search
10. get searches
11. delete search

It also exercises all 28 World routes exposed by the current documentation and
service:

1. events by day
2. entity events
3. ticker events
4. ontology events
5. all-time search
6. aggregate
7. resolve
8. version
9. dates
10. entity summary
11. ticker details
12. search schema
13. dated autocomplete
14. dated semantic search
15. dated structured search
16. snapshot
17. event detail
18. similar events
19. event aggregates
20. event coverage
21. Markdown daily index
22. Markdown today
23. Markdown yesterday
24. Markdown resolve
25. Markdown entity
26. Markdown ticker
27. Markdown event
28. Markdown bulk ZIP

## Running only this contract

```powershell
$env:PYTHONPATH = "src"
python -m pytest -o addopts="" tests/contract -q
```

The command must collect without credentials or network access. A release
candidate is ready only when this suite and the existing compatibility suite
both pass.
