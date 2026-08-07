# Changelog

## 0.4.0 — 2026-07-30

### Added

- Complete NOSIBLE Search API v2.1 coverage, including Rich, Time, saved
  searches, limits, and current Search filters.
- `Nosible.world`, with typed access to all documented World routes.
- Lossless `RichResult`, `WorldEvent`, and `WorldEventPage` models.
- Stable `NosibleAPIError` subclasses with HTTP and retry metadata.
- Configurable `base_url` and injected `httpx.Client` support.
- Offline Search and World contract tests built from the OpenAPI definition,
  endpoint data dictionaries, and checked-in World service source.

### Changed

- Search and World now share the merged `https://nosible.world/api` origin.
- Search responses preserve v2.1 retrieval diagnostics and unknown fields.
- ResultSet CSV round trips preserve nested values, unknown fields, scalar
  types, explicit nulls, and omitted fields while retaining legacy CSV read
  compatibility.
- Scrape snippets preserve every documented media/content block and unknown
  future fields.
- Bulk and Time Search poll and decode encrypted Zstandard payloads while
  retaining legacy gzip compatibility.
- Client construction no longer performs network I/O to discover limits.
  Call `get_limits()` explicitly when current quota data is needed.
- `fast_searches` forwards Search v2.1 filters to every request.
- `fast_searches` now forwards shared options consistently for question
  batches, `list[Search]`, and `SearchSet` inputs.
- Safe read requests retry HTTP 429 and transient 5xx responses and honor
  numeric or HTTP-date `Retry-After` headers.
- Presigned Bulk and Time downloads use the same transient-status retry
  policy while preserving 404 polling semantics.
- Sparse `Snippet` payloads now round-trip omitted fields and explicit nulls
  exactly.
- `WorldClient.similar_events` accepts the documented optional `floor`
  parameter.
- Importing `nosible` no longer configures or disables application logging.
- CI now gates releases on offline tests, Ruff, and a strict documentation
  build instead of ignoring failures from live HTTP recording jobs. PyPI
  publishing requires an exact `v<package-version>` tag and uses trusted
  publishing.
- Package license metadata remains compatible with the declared minimum
  setuptools version.
- CI enforces the NOSIBLE Python rules across production code, tests, helper
  scripts, and Sphinx configuration.
- Search Schema and Markdown delivery requests are public-first. When a
  deployment rejects anonymous access, the SDK retries once with SDK-managed
  bearer authentication if an API key is configured.
- `fast_searches` again executes batches concurrently while preserving input
  order and respecting the configured concurrency limit.

### Compatibility

- Existing Search, Result, ResultSet, SearchSet, Snippet, and WebPageData
  symbols remain public.
- Search calls still use the `api-key` header; authenticated World calls use
  bearer authentication. World version remains strictly credential-free;
  Search Schema and Markdown delivery routes retain their public contract with
  the deployment-compatibility fallback described above.
- API errors remain compatible with existing `ValueError` handlers.
- `fast_search(n_results=1..9)` retains the legacy convenience behavior by
  requesting the server minimum of 10 and truncating locally.

### Security

- Presigned download requests explicitly disable authentication configured on
  an injected `httpx.Client`, preventing client-level bearer credentials from
  reaching an object-storage host.
- Every SDK-managed request replaces credentials configured on an injected
  `httpx.Client`, preventing stale or wrong-scheme client authentication from
  overriding endpoint-specific SDK authentication.
