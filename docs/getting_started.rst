Getting Started
===============

A high-level Python client for the `NOSIBLE Search
API <https://www.nosible.ai/search/v1/docs/swagger#/>`__. Easily
integrate the Nosible Search API into your Python projects.

📦 Installation
~~~~~~~~~~~~~~~

.. code:: bash

   pip install nosible

**Requirements**:

-  Python 3.9+
-  requests
-  polars
-  cryptography
-  tenacity
-  pyrate-limiter
-  tantivy
-  openai

🔑 Authentication
~~~~~~~~~~~~~~~~~

1. Sign in to NOSIBLE.AI and grab your free API key.
2. Set it as an environment variable or pass directly:

On Windows

.. code:: powershell

   $Env:NOSIBLE_API_KEY="basic|abcd1234..."
   $Env:LLM_API_KEY="sk-..."  # for query expansions (optional)

On Linux

.. code:: bash

   export NOSIBLE_API_KEY="basic|abcd1234..."
   export LLM_API_KEY="sk-..."  # for query expansions (optional)

Or in code:

- As an argument:

.. code:: python

   from nosible import Nosible

   client = Nosible(
       nosible_api_key="basic|abcd1234...",
       llm_api_key="sk-...",
   )

- As an environment variable:

.. code:: python

   from nosible import Nosible
   import os

   os.environ["NOSIBLE_API_KEY"] = "basic|abcd1234..."
   os.environ["LLM_API_KEY"] = "sk-..."

🎯 Core Workflows
~~~~~~~~~~~~~~~~~

+-------------------------------+-------------+-----------------------+
| I need                        | Method      | Use case              |
+===============================+=============+=======================+
| Single query, up to 100       | ``search``  | Interactive lookups   |
| results                       |             |                       |
+-------------------------------+-------------+-----------------------+
| Multiple queries in parallel  |``searches`` | Dashboards,           |
|                               |             | comparisons           |
+-------------------------------+-------------+-----------------------+
| Thousands of results          | ``bu        | Analytics, offline    |
| (100–10k)                     | lk_search`` | jobs                  |
+-------------------------------+-------------+-----------------------+

--------------

🚀 Examples
~~~~~~~~~~~

Fast Search
^^^^^^^^^^^

Retrieve up to 100 results with optional filters:

.. code:: python

   from nosible import Nosible

   with Nosible(
       nosible_api_key="basic|abcd1234...",
       llm_api_key="sk-...",
       base_url="https://api.openrouter.ai/v1"
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

Parallel Searches
^^^^^^^^^^^^^^^^^

Run multiple queries concurrently:

.. code:: python

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

Bulk Search
^^^^^^^^^^^

Fetch thousands of results for offline analysis:

.. code:: python

   from nosible import Nosible

   with Nosible(nosible_api_key="basic|abcd1234...") as client:
       bulk = client.bulk_search(
           question="What chip-development responsibilities has Intel committed to under its deal with Apple?",
           n_results=2000
       )
       print(len(bulk))
   print(bulk)

Combine Results
^^^^^^^^^^^^^^^

Add two ResultSets together:

.. code:: python

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

Search Object
^^^^^^^^^^^^^

Use the ``Search`` class to encapsulate parameters:

.. code:: python

   from nosible import Nosible, Search

   with Nosible(nosible_api_key="basic|abcd1234...") as client:
       search = Search(
           question="What are the terms of the partnership between Microsoft and OpenAI?",
           n_results=3,
           publish_start="2025-01-15",
           publish_end="2025-06-20",
           include_netlocs=["arxiv.org", "bbc.com"],
           certain=True
       )
       results = client.search(search=search)
       print([r for r in results])

Sentiment Analysis
^^^^^^^^^^^^^^^^^^

Compute sentiment for a single result (uses GPT-4o; requires LLM API
key):

.. code:: python

   from nosible import Nosible

   with Nosible(nosible_api_key="basic|abcd1234...", llm_api_key="sk-...") as client:
       results = client.search(
           question="What are the terms of the partnership between Microsoft and OpenAI?",
           n_results=1
       )
       score = results[0].sentiment(client)
       print(f"Sentiment score: {score:.2f}")

Save & Load Formats
^^^^^^^^^^^^^^^^^^^

Supported formats for saving and loading:

.. code:: python

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

--------------

📡 Swagger Docs
~~~~~~~~~~~~~~~

You can find online endpoints to the NOSIBLE Search API Swagger Docs
`here <https://www.nosible.ai/search/v1/docs/swagger#/>`__.

--------------
