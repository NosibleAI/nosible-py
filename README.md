[![Linux Tests](https://github.com/NosibleAI/nosible-py/actions/workflows/tests-linux.yml/badge.svg?branch=main)](https://github.com/NosibleAI/nosible-py/actions/workflows/tests-linux.yml)
[![Windows Tests](https://github.com/NosibleAI/nosible-py/actions/workflows/tests-windows.yml/badge.svg?branch=main)](https://github.com/NosibleAI/nosible-py/actions/workflows/tests-windows.yml)
[![macOS Tests](https://github.com/NosibleAI/nosible-py/actions/workflows/tests-macos.yml/badge.svg?branch=main)](https://github.com/NosibleAI/nosible-py/actions/workflows/tests-macos.yml)
[![Read the Docs](https://img.shields.io/readthedocs/nosible-py/latest.svg?label=docs&logo=readthedocs)](https://nosible-py.readthedocs.io/en/latest/)


![Logo](./docs/_static/readme.png)

# NOSIBLE Search Client

A high-level Python client for the [NOSIBLE Search API](https://www.nosible.ai/search/v1/docs/swagger#/).
Easily integrate the Nosible Search API into your Python projects.

### 📦 Installation

```bash
pip install nosible
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

### ⚙️ Configuration

You can specify a custom base URL for all endpoints (e.g., OpenRouter, Google, or your own proxy):

```python
from nosible import Nosible

client = Nosible(
    nosible_api_key="basic|abcd1234…",
    llm_api_key="sk-…",
    base_url="https://api.openrouter.ai/v1"
)
```

### 🔑 Authentication

1. Sign in to nosible.ai and grab your free API key.
2. Set it as an environment variable or pass directly:


On Windows

```powershell
$Env:NOSIBLE_API_KEY="basic|abcd1234…"
$Env:LLM_API_KEY="sk-…"  # for query expansions (optional)
```

On Linux
```bash
export NOSIBLE_API_KEY="basic|abcd1234…"
export LLM_API_KEY="sk-…"  # for query expansions (optional)
```

Or in code:
```python
from nosible import Nosible

client = Nosible(
    nosible_api_key="basic|abcd1234…",
    llm_api_key="sk-…",
)
```

### 🎯 Core Workflows

| I need                          | Method        | Use case                |
|---------------------------------|---------------|-------------------------|
| Single query, up to 100 results | `search`      | Interactive lookups     |
| Multiple queries in parallel    | `searches`    | Dashboards, comparisons |
| Thousands of results (100–10k)  | `bulk_search` | Analytics, offline jobs |

---

### 🚀 Examples

#### Fast Search

Retrieve up to 100 results with optional filters:

```python
from nosible import Nosible

with Nosible(
    nosible_api_key="basic|abcd1234…",
    llm_api_key="sk-…",
    base_url="https://api.openrouter.ai/v1"
) as client:
    results = client.search(
        question="What are the terms of the partnership between Microsoft and OpenAI?",
        n_results=20,
        publish_start="2025-06-01",
        publish_end="2025-06-30",
        include_netlocs=["nytimes.com", "techcrunch.com"],
        exclude_netlocs=["example.com"],
        visited_start="2025-06-01",
        visited_end="2025-06-29",
        include_languages=["en", "fr"],
        exclude_languages=["de"],
        include_companies=["/g/11bxc656v6"],  # OpenAI GKID
        exclude_companies=["/m/045c7b"]       # Google GKID
    )
    print([r.title for r in results])
```

#### Parallel Searches

Run multiple queries concurrently:

```python
from nosible import Nosible

with Nosible(nosible_api_key="basic|abcd1234…", llm_api_key="sk-…") as client:
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

with Nosible(nosible_api_key="basic|abcd1234…") as client:
    bulk = client.bulk_search(
        question="What chip-development responsibilities has Intel committed to under its deal with Apple?",
        n_results=2000
    )
    print(len(bulk))  # e.g., 2000
print(len(bulk))  # e.g., 2000
```

#### Combine Results

Add two ResultSets together:

```python
from nosible import Nosible

with Nosible(nosible_api_key="basic|abcd1234…") as client:
    r1 = client.search(
        question="What are the terms of the partnership between Microsoft and OpenAI?",
        n_results=5
    )
    r2 = client.search(
        question="How is research governance and decision-making structured between Google and DeepMind?",
        n_results=5
    )
    combined = r1 + r2
    print(len(combined))  # 10
```

#### Search Object

Use the `Search` class to encapsulate parameters:

```python
from nosible import Nosible, Search

with Nosible(nosible_api_key="basic|abcd1234…") as client:
    params = Search(
        question="What are the terms of the partnership between Microsoft and OpenAI?",
        n_results=3,
        publish_start="2025-06-15",
        publish_end="2025-06-20",
        include_netlocs=["arxiv.org"],
        certain=True
    )
    results = client.search(params)
    print([r.idx for r in results])
```

#### Sentiment Analysis

Compute sentiment for a single result (Uses GPT-4o; requires LLM API key):

```python
from nosible import Nosible

with Nosible(nosible_api_key="basic|abcd1234…", llm_api_key="sk-…") as client:
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

with Nosible(nosible_api_key="basic|abcd1234…") as client:
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
    rs_duckdb = ResultSet.from_duckdb("all_news.duckdb", table_name="news")
    rs_ndjson = ResultSet.from_ndjson("all_news.ndjson")
```

---


### ⚙️ Rate Limiting

Inspect your current limits at runtime:

```python
client.get_ratelimits()
```
Default limits by plan:

| Plan           | Period     | Fast Searches | URL Visits | Slow Searches | Cost     | CPM  |
|----------------|------------|---------------|------------|---------------|----------|------|
| **Free**       | Monthly    | 3,000         | 300        | 300           | \$0      | $0   |
|                | Daily      | 100           | 10         | 10            |          |      |
|                | Per-Minute | 10            | 1          | 1             |          |      |
| **Basic**      | Monthly    | 30,000        | 3,000      | 3,000         | \$120    | $4   |
|                | Daily      | 1,000         | 100        | 100           |          |      |
|                | Per-Minute | 10            | 1          | 1             |          |      |
| **Pro**        | Monthly    | 150,000       | 7,500      | 7,500         | \$450    | $3   |
|                | Daily      | 5,000         | 250        | 250           |          |      |
|                | Per-Minute | 10            | 1          | 1             |          |      |
| **Pro+**       | Monthly    | 300,000       | 15,000     | 15,000        | \$750    | $2.5 |
|                | Daily      | 10,000        | 500        | 500           |          |      |
|                | Per-Minute | 10            | 2          | 1             |          |      |
| **Business**   | Monthly    | 1,500,000     | 30,000     | 30,000        | \$3,000  | $2   |
|                | Daily      | 50,000        | 1,000      | 1,000         |          |      |
|                | Per-Minute | 35            | 2          | 2             |          |      |
| **Business+**  | Monthly    | 3,000,000     | 60,000     | 60,000        | \$4,500  | $1.5 |
|                | Daily      | 100,000       | 2,000      | 2,000         |          |      |
|                | Per-Minute | 100           | 3          | 3             |          |      |
| **Enterprise** | Monthly    | 15,000,000    | 150,000    | 150,000       | \$15,000 | $1   |
|                | Daily      | 500,000       | 5,000      | 5,000         |          |      |
|                | Per-Minute | 400           | 5          | 5             |          |      |

*All endpoints are automatically throttled

---

© 2025 Nosible Inc. | [Privacy Policy](https://www.nosible.ai/privacy) | [Terms](https://www.nosible.ai/terms)
