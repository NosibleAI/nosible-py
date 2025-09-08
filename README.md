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

A high-level Python client for the [NOSIBLE Search API](https://www.nosible.ai/search/v2/docs/#/).
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

### 🔍 Your first search

To complete your first search:

```python
from nosible import Nosible

with Nosible(nosible_api_key="YOUR API KEY") as client:

    results = client.fast_search(
        question="What is Artificial General Intelligence?"
    )

    print(results)
```

### 🤖 Cybernaut 1

An AI agent with unrestricted access to everything in NOSIBLE including every shard, algorithm, selector, 
reranker, and signal. It knows what these things are and can tune them on the fly to find better results.

```python
from nosible import Nosible

with Nosible(nosible_api_key="YOUR API KEY") as client:

    results = client.search(
        # search() gives you access to Cybernaut 1
        question="Find me interesting technical blogs about Monte Carlo Tree Search."
    )

    print(results)
```

### 📄 Documentation

You can find the full NOSIBLE Search Client documentation 
[here](https://nosible-py.readthedocs.io/).

### 📡 Swagger Docs

You can find online endpoints to the NOSIBLE Search API Swagger Docs
[here](https://www.nosible.ai/search/v2/docs/#/).


---

© 2025 Nosible Inc. | [Privacy Policy](https://www.nosible.ai/privacy) | [Terms](https://www.nosible.ai/terms)


[nosible-badge]: https://img.shields.io/static/v1?label=Visit&message=nosible.ai&\style=flat&logoUri=https://raw.githubusercontent.com/NosibleAI/nosible-py/main/docs/_static/favicon.png&logoWidth=20