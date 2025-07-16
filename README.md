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
* polars
* duckdb
* openai
* tantivy
* pyrate-limiter
* tenacity
* cryptography
* pyarrow
* pandas

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

#### Search

The Search and Searches functions enables you to retrieve **up to 100** results for a single query. This is ideal for most use cases where you need to retrieve information quickly and efficiently.

- Use the `search` method when you need between **10 and 100** results for a single query.
- The same applies for the `searches` and `.similar()` methods.

- A search will return a set of `Result` objects.
- The `Result` object is used to represent a single search result and provides methods to access the result's properties.
    - `url`: The URL of the search result.
    - `title`: The title of the search result.
    - `description`: A brief description or summary of the search result.
    - `netloc`: The network location (domain) of the URL.
    - `published`: The publication date of the search result.
    - `visited`: The date and time when the result was visited.
    - `author`: The author of the content.
    - `content`: The main content or body of the search result.
    - `language`: The language code of the content (e.g., 'en' for English).
    - `similarity`: Similarity score with respect to a query or reference.

They can be accessed directly from the `Result` object: `print(result.title)` or
`print(result["title"])`

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

#### Expansions

**Prompt expansions** are questions **lexically** and **semantically similar** to your main question. Expansions are added alongside your search query to improve your search results. You can add up to 10 expansions per search.

- You can add you **own expansions** by passing a list of strings to the `expansions` parameter.
- You can also get your expansions automatically generated by setting `autogenerate_expansions` to `True` when running the search.
    - For expansions to be generated, you will need the `LLM_API_KEY` to be set in the environment or passed to the `Nosible` constructor.
      - By default, we use openrouter as an endpoint. However, **we support any endpoint that supports openai**. If you 
        want to use a different endpoint, follow [this](https://nosible-py.readthedocs.io/en/latest/configuration.html#change-llm-base-url) guide in the docs.
    - You can change this model with the argument **expansions_model**.

```python
# Example of using your own expansions
with Nosible() as nos:
    results = nos.search(
        question="How have the Trump tariffs impacted the US economy?",
        expansions=[
            "What are the consequences of Trump's 2018 steel and aluminum tariffs on American manufacturers?",
            "How did Donald Trump's tariffs on Chinese imports influence US import prices and inflation?",
            "What impact did the Section 232 tariffs under President Trump have on US agricultural exports?",
            "In what ways have Trump's trade duties affected employment levels in the US automotive sector?",
            "How have the tariffs imposed by the Trump administration altered American consumer goods pricing nationwide?",
            "What economic outcomes resulted from President Trump's protective tariffs for the United States economy?",
            "How did Trump's solar panel tariffs change investment trends in the US energy market?",
            "What have been the financial effects of Trump's Section 301 tariffs on Chinese electronics imports?",
            "How did Trump's trade barriers influence GDP growth and trade deficits in the United States?",
            "In what manner did Donald Trump's import taxes reshape competitiveness of US steel producers globally?",
        ],
        n_results=10,
    )

print(results)
```

#### Parallel Searches

Allows you to run multiple searches concurrently and `yields` the results as they come in.
- You can pass a list of questions to the `searches` method.

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

Bulk search enables you to retrieve a large number of results in a single request, making it ideal for large-scale data analysis and processing.

- Use the `bulk_search` method when you need more than 1,000 results for a single query.
- You can request between **1,000 and 10,000** results per query.
- All parameters available in the standard `search` method—such as `expansions`, `include_companies`, `include_languages`, and more—are also supported in `bulk_search`.
- A bulk search for 10,000 results typically completes in about 30 seconds or less.

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

#### Sentiment

This fetches a sentiment score for each search result.
- The sentiment score is a float between `-1` and `1`, where `-1` is **negative**, `0` is **neutral**, and `1` is **positive**.
- The sentiment model can be changed by passing the `sentiment_model` parameter to the `Nosible` constructor.
    - The `sentiment_model` defaults to "openai/gpt-4o", which is a powerful model for sentiment analysis.
- You can also change the base URL for the LLM API by passing the `openai_base_url` parameter to the `Nosible` constructor.
    - The `openai_base_url` defaults to OpenRouter's API endpoint.

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