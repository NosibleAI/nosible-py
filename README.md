[![Tests](https://img.shields.io/github/actions/workflow/status/NosibleAI/nosible-py/run_tests_and_publish.yml?branch=main&label=tests)](https://github.com/NosibleAI/nosible-py/actions/workflows/run_tests_and_publish.yml)
[![Documentation](https://img.shields.io/readthedocs/nosible-py/latest.svg?label=docs&logo=readthedocs)](https://nosible-py.readthedocs.io/)
[![PyPI](https://img.shields.io/pypi/v/nosible.svg?label=PyPI&logo=python)](https://pypi.org/project/nosible/)

![NOSIBLE](https://github.com/NosibleAI/nosible-py/blob/main/docs/_static/readme.png?raw=true)

# NOSIBLE Python SDK

`nosible` is the official synchronous Python SDK for NOSIBLE's worldwide
web-surveillance platform. It provides **SEARCH** for retrieving dated, ranked
web sources and **WORLD** for accessing structured, point-in-time verified
events for models, research, and backtesting.

Version 0.4.0 supports every [SEARCH v2.1](https://docs.nosible.com/)
endpoint and exposes [WORLD](https://nosible.world/) through the
`client.world` namespace. Existing 0.3 Search models and convenience methods
remain available.

## Installation

```bash
pip install "nosible==0.4.0"
```

Python 3.9 or newer is supported.

## Authentication

Create an API key at [app.nosible.com](https://app.nosible.com/), then set
`NOSIBLE_API_KEY` or pass the key to the client.

```powershell
$Env:NOSIBLE_API_KEY="nos_sk_..."
```

```python
from nosible import Nosible

client = Nosible()
# Or: client = Nosible(nosible_api_key="nos_sk_...")
```

Search uses the `api-key` request header. Authenticated World routes use bearer
authentication. World version is public and always credential-free. Search
Schema and Markdown delivery requests are sent without credentials first; if a
deployment responds with an authentication error, the SDK retries once with
SDK-managed bearer authentication when an API key is configured. Credentials
configured on an injected HTTP client are replaced for every SDK request and
are never forwarded to presigned Bulk and Time Search download URLs.

## Search v2.1

```python
from nosible import Nosible

with Nosible() as client:
    results = client.fast_search(
        question="What is changing in semiconductor capacity?",
        companies=["NVIDIA", "TSMC"],
        collection="this-week",
        deduplicate=True,
        n_results=25
    )

    for result in results:
        print(result.title, result.similarity, result.url)
```

The client covers all 11 Search endpoints:

- `search` for Cybernaut agentic search
- `fast_search` and `fast_searches`
- `rich_search`
- `bulk_search`
- `time_search`
- `scrape_url`
- `topic_trend`
- `save_search`, `get_searches`, and `delete_search`
- `get_limits`

Bulk and Time Search handle polling, Fernet decryption, and current Zstandard
or legacy gzip payloads. `bulk_search` returns a `ResultSet`; `time_search`
preserves the interval-bucket response. Transient download responses are
retried, and authentication configured on an injected `httpx.Client` is
explicitly disabled for presigned download hosts.

`fast_searches` accepts question strings, `list[Search]`, or `SearchSet`.
Shared filters and retrieval options are applied consistently to every search
whose model does not override them. Non-null model values take precedence,
including `False` for the optional `certain` filter. Expansion generation is
enabled when either the batch or the individual model opts in. Requests run
concurrently up to the client's configured `concurrency` while results retain
input order.

For compatibility, Fast Search defaults to 100 results and 128 context tokens,
while the service schema defaults are 10 and 256. Requests for fewer than 10
results are truncated locally.

## World

```python
from nosible import Nosible

with Nosible() as client:
    page = client.world.entity_events(
        entity_type="ORG",
        name="NVIDIA",
        from_="2026-07-01",
        to="2026-07-20",
        include="event_lite",
        include_live=True
    )

    for event in page:
        print(event.event_id, event.event["title"])

    neighbors = client.world.similar_events(
        date="2026-07-20",
        event_id=page[0].event_id,
        floor=0.35
    )
```

`client.world` covers dated events, entity/ticker/ontology timelines, global
search and aggregation, resolve and metadata routes, dated search, event
details and coverage, snapshots, and all Markdown delivery routes.
`WorldEvent` and `WorldEventPage` preserve unknown fields so newer server
schemas can round-trip without data loss. `Snippet` does the same for Search
scrape payloads, including the distinction between an omitted field and an
explicit null.

## Errors and custom transports

HTTP failures raise subclasses of `NosibleAPIError`, which remains a
`ValueError` for backwards compatibility. Errors expose `status_code`,
`code`, `method`, `path`, `body`, and `retry_after`.

An `httpx.Client` and alternate merged API origin can be injected for testing
or private deployments:

```python
import httpx
from nosible import Nosible

http = httpx.Client()
client = Nosible(
    base_url="https://staging.example/api",
    http_client=http
)
client.close()  # Does not close an injected client.
http.close()
```

## Reference

- [Combined API documentation](https://docs.nosible.com/)
- [Search data dictionaries](https://nosible.com/data-dictionaries)
- [Python SDK documentation](https://nosible-py.readthedocs.io/)
- [Start a trial](https://nosible.com/start-trial)

© 2026 NOSIBLE Inc. [Privacy](https://nosible.com/privacy) ·
[Terms](https://nosible.com/terms)
