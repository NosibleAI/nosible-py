[![Linux Tests](https://img.shields.io/github/actions/workflow/status/NosibleAI/nosible-py/run_tests_and_publish.yml?branch=main&label=Linux%20Tests)](https://github.com/NosibleAI/nosible-py/actions/workflows/run_tests_and_publish.yml)
[![Windows Tests](https://img.shields.io/github/actions/workflow/status/NosibleAI/nosible-py/run_tests_and_publish.yml?branch=main&label=Windows%20Tests)](https://github.com/NosibleAI/nosible-py/actions/workflows/run_tests_and_publish.yml)
[![macOS Tests](https://img.shields.io/github/actions/workflow/status/NosibleAI/nosible-py/run_tests_and_publish.yml?branch=main&label=macOS%20Tests)](https://github.com/NosibleAI/nosible-py/actions/workflows/run_tests_and_publish.yml)
[![Read the Docs](https://img.shields.io/readthedocs/nosible-py/latest.svg?label=docs&logo=readthedocs)](https://nosible-py.readthedocs.io/en/latest/)
[![PyPI version](https://img.shields.io/pypi/v/nosible.svg?label=PyPI&logo=python)](https://pypi.org/project/nosible/)
[![codecov](https://codecov.io/gh/NosibleAI/nosible-py/graph/badge.svg?token=DDXGQ3V6P9)](https://codecov.io/gh/NosibleAI/nosible-py)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/nosible.svg)](https://pypi.org)


[//]: # ([![Visit Nosible]&#40;https://img.shields.io/static/v1?label=Visit&message=nosible.ai&style=flat&logoUri=https://www.nosible.ai/assests/favicon.png&logoWidth=20&#41;]&#40;https://www.nosible.ai/&#41;)

![Logo](https://github.com/NosibleAI/nosible-py/blob/main/docs/_static/readme.png?raw=true)

# NOSIBLE Search Client

A high-level Python client for the [NOSIBLE Search API](https://www.nosible.ai/search/v1/docs/swagger#/).
Easily integrate the Nosible Search API into your Python projects.

### 📄 Documentation

You can find the full NOSIBLE Search Client documentation 
[here](https://nosible-py.readthedocs.io/).

### 📦 Installation

```bash
pip install nosible
```

### ⚡ Installing with uv 

```bash
uv pip install nosible
```

**Requirements**:

* Python 3.9+
* requests
* polars
* cryptography
* tenacity
* pyrate-limiter
* tantivy
* openai

### 🔑 Authentication

1. Sign in to [NOSIBLE.AI](https://www.nosible.ai/) and grab your free API key.
2. Set it as an environment variable or pass directly:

On Windows

```powershell
$Env:NOSIBLE_API_KEY="basic|abcd1234..."
$Env:LLM_API_KEY="sk-..."  # for query expansions (optional)
```

On Linux
```bash
export NOSIBLE_API_KEY="basic|abcd1234..."
export LLM_API_KEY="sk-..."  # for query expansions (optional)
```

Or in code:

- As an argument:

```python
from nosible import Nosible

client = Nosible(
    nosible_api_key="basic|abcd1234...",
    llm_api_key="sk-...",
)
```

- As an environment variable:

```python
from nosible import Nosible
import os

os.environ["NOSIBLE_API_KEY"] = "basic|abcd1234..."
os.environ["LLM_API_KEY"] = "sk-..."
```

### 🎯 Core Workflows

| I need                          | Method        | Use case                |
|---------------------------------|---------------|-------------------------|
| Single query, up to 100 results | `search`      | Interactive lookups     |
| Multiple queries in parallel    | `searches`    | Dashboards, comparisons |
| Thousands of results (100–10k)  | `bulk_search` | Analytics, offline jobs |


### 🚀 Examples

#### Fast Search

Retrieve up to 100 results with optional filters:

```python
from nosible import Nosible

with Nosible(
    nosible_api_key="basic|abcd1234...",
    llm_api_key="sk-...",
    openai_base_url="https://api.openrouter.ai/v1"
) as client:
    results = client.search(
        question="What are the terms of the partnership between Microsoft and OpenAI?",
        n_results=20,
        publish_start="2020-06-01",
        publish_end="2025-06-30",
        include_netlocs=["nytimes.com", "techcrunch.com"],
        exclude_netlocs=["example.com"],
        visited_start="2023-06-01",
        visited_end="2025-06-29",
        include_languages=["en", "fr"],
        exclude_languages=["de"],
        include_companies=["/m/04sv4"],  # Microsoft's GKID
        exclude_companies=["/m/045c7b"]  # Google GKID
    )
    print([r.title for r in results])
```

#### Parallel Searches

Run multiple queries concurrently:

```python
from nosible import Nosible

with Nosible(nosible_api_key="basic|abcd1234...", llm_api_key="sk-...") as client:
    for batch in client.searches(
        questions=[
            "What are the terms of the partnership between Microsoft and OpenAI?",
            "What exclusivity or non-compete clauses are included in their partnership?"
        ],
        n_results=10,
        publish_start="2025-06-01"
    ):
        print(batch[0].title)
```

#### Bulk Search

Fetch thousands of results for offline analysis:

```python
from nosible import Nosible

with Nosible(nosible_api_key="basic|abcd1234...") as client:
    bulk = client.bulk_search(
        question="What chip-development responsibilities has Intel committed to under its deal with Apple?",
        n_results=2000
    )
    print(len(bulk))
print(bulk)
```

#### Combine Results

Add two ResultSets together:

```python
from nosible import Nosible

with Nosible(nosible_api_key="basic|abcd1234...") as client:
    r1 = client.search(
        question="What are the terms of the partnership between Microsoft and OpenAI?",
        n_results=5
    )
    r2 = client.search(
        question="How is research governance and decision-making structured between Google and DeepMind?",
        n_results=5
    )
    combined = r1 + r2
    print(combined)
```

#### Search Object

Use the `Search` class to encapsulate parameters:

```python
from nosible import Nosible, Search

with Nosible(nosible_api_key="basic|abcd1234...") as client:
    search = Search(
        question="What are the terms of the partnership between Microsoft and OpenAI?",
        n_results=3,
        publish_start="2020-01-15",
        publish_end="2025-07-20",
        include_netlocs=["arxiv.org", "bbc.com"],
        certain=True
    )
    results = client.search(search=search)
    print([r for r in results])
```

#### Sentiment Analysis

Compute sentiment for a single result (uses GPT-4o; requires an LLM API key):

```python
from nosible import Nosible

with Nosible(nosible_api_key="basic|abcd1234...", llm_api_key="sk-...") as client:
    results = client.search(
        question="What are the terms of the partnership between Microsoft and OpenAI?",
        n_results=1
    )
    score = results[0].sentiment(client)
    print(f"Sentiment score: {score:.2f}")
```

#### Save & Load Formats

Supported formats for saving and loading:

```python
from nosible import Nosible, ResultSet

with Nosible(nosible_api_key="basic|abcd1234...") as client:
    combined = client.search(
        question="What are the terms of the partnership between Microsoft and OpenAI?",
        n_results=5
    ) + client.search(
        question="How is research governance and decision-making structured between Google and DeepMind?",
        n_results=5
    )

    # Save
    combined.to_csv("all_news.csv")
    combined.to_json("all_news.json")
    combined.to_parquet("all_news.parquet")
    combined.to_arrow("all_news.arrow")
    combined.to_duckdb("all_news.duckdb", table_name="news")
    combined.to_ndjson("all_news.ndjson")

    # Load
    rs_csv    = ResultSet.from_csv("all_news.csv")
    rs_json   = ResultSet.from_json("all_news.json")
    rs_parq   = ResultSet.from_parquet("all_news.parquet")
    rs_arrow  = ResultSet.from_arrow("all_news.arrow")
    rs_duckdb = ResultSet.from_duckdb("all_news.duckdb")
    rs_ndjson = ResultSet.from_ndjson("all_news.ndjson")
```

#### More Examples

For more examples, checkout `/examples` for in-depth usage of the NOSIBLE Client Package

### 📡 Swagger Docs

You can find online endpoints to the NOSIBLE Search API Swagger Docs
[here](https://www.nosible.ai/search/v1/docs/swagger#/).

### ⚙️ Rate Limiting

Inspect your current limits at runtime:

```python
client.get_ratelimits()
```

Or you can view them on the [docs](https://nosible-py.readthedocs.io/en/latest/rate_limits.html).

---

© 2025 Nosible Inc. | [Privacy Policy](https://www.nosible.ai/privacy) | [Terms](https://www.nosible.ai/terms)


[nosible-badge]: https://img.shields.io/static/v1?label=Visit&message=nosible.ai&\style=flat&logoUri=https://raw.githubusercontent.com/NosibleAI/nosible-py/main/docs/_static/favicon.png&logoWidth=20