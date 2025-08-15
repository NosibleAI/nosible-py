Getting Started
===============

A high-level Python client for the `NOSIBLE Search
API <https://www.nosible.ai/search/v1/docs/swagger#/>`__. Easily
integrate the Nosible Search API into your Python projects.

📦 Installation
~~~~~~~~~~~~~~~

.. code:: bash

   pip install nosible


⚡ Installing with uv 
~~~~~~~~~~~~~~~~~~~~~

.. code:: bash
    uv pip install nosible


**Requirements**:

- Python 3.9+
- polars
- duckdb
- openai
- tantivy
- pyrate-limiter
- tenacity
- cryptography
- pyarrow
- pandas

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

Search
^^^^^^

The Search and Searches functions enables you to retrieve **up to 100** results for a single query. This is ideal for most use cases where you need to retrieve information quickly and efficiently.

- Use the ``search`` method when you need between **10 and 100** results for a single query.
- The same applies for the ``searches`` and ``.similar()`` methods.

- A search will return a set of ``Result`` objects.
- The ``Result`` object is used to represent a single search result and provides methods to access the result’s properties:
  - ``url``: The URL of the search result.
  - ``title``: The title of the search result.
  - ``description``: A brief description or summary of the search result.
  - ``netloc``: The network location (domain) of the URL.
  - ``published``: The publication date of the search result.
  - ``visited``: The date and time when the result was visited.
  - ``author``: The author of the content.
  - ``content``: The main content or body of the search result.
  - ``language``: The language code of the content (e.g., ‘en’ for English).
  - ``similarity``: Similarity score with respect to a query or reference.

They can be accessed directly from the ``Result`` object (e.g. ``print(result.title)`` or ``print(result["title"])``.

.. code:: python

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
           include_companies=["/m/04sv4"],  # Microsoft's GKID
           exclude_companies=["/m/045c7b"]  # Google GKID
       )
       print([r.title for r in results])

Parallel Searches
^^^^^^^^^^^^^^^^^

Allows you to run multiple searches concurrently and ``yields`` the results as they come in.

- You can pass a list of questions to the ``searches`` method.

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

Expansions
^^^^^^^^^^

**Prompt expansions** are questions **lexically** and **semantically similar** to your main question.  Expansions are added alongside your search query to improve your search results.  You can add up to 10 expansions per search.

- You can add your **own expansions** by passing a list of strings to the ``expansions`` parameter.
- You can also get your expansions automatically generated by setting ``autogenerate_expansions`` to ``True`` when running the search.
   - For expansions to be generated, you will need the ``LLM_API_KEY`` to be set in the environment or passed to the ``Nosible`` constructor.
   - You can change this model with the argument ``expansions_model``.

.. code:: python

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


Bulk Search
^^^^^^^^^^^

Bulk search enables you to retrieve a large number of results in a single request, making it ideal for large-scale data analysis and processing.

- Use the ``bulk_search`` method when you need more than 1,000 results for a single query.
- You can request between **1,000 and 10,000** results per query.
- All parameters available in the standard ``search`` method—such as ``expansions``, ``include_companies``, and more—are also supported in ``bulk_search``.
- A bulk search for 10,000 results typically completes in about 30 seconds or less.

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

This fetches a sentiment score for each search result.

- The sentiment score is a float between ``-1`` and ``1``, where ``-1`` is **negative**, ``0`` is **neutral**, and ``1`` is **positive**.
- The sentiment model can be changed by passing the ``sentiment_model`` parameter to the ``Nosible`` constructor.
  - The ``sentiment_model`` defaults to “openai/gpt-4o”, which is a powerful model for sentiment analysis.
- You can also change the base URL for the LLM API by passing the ``openai_base_url`` parameter to the ``Nosible`` constructor.
  - The ``openai_base_url`` defaults to OpenRouter’s API endpoint.

Compute sentiment for a single result (uses GPT-4o; requires LLM API key):

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
       combined.write_csv("all_news.csv")
       combined.write_json("all_news.json")
       combined.write_parquet("all_news.parquet")
       combined.write_ipc("all_news.ipc")
       combined.write_duckdb("all_news.duckdb", table_name="news")
       combined.write_ndjson("all_news.ndjson")

       # Load
       rs_csv    = ResultSet.read_csv("all_news.csv")
       rs_json   = ResultSet.read_json("all_news.json")
       rs_parq   = ResultSet.read_parquet("all_news.parquet")
       rs_arrow  = ResultSet.read_ipc("all_news.ipc")
       rs_duckdb = ResultSet.read_duckdb("all_news.duckdb")
       rs_ndjson = ResultSet.read_ndjson("all_news.ndjson")

Find in Search Results
^^^^^^^^^^^^^^^^^^^^^^

This allows you to search within the results of a search using BM25 scoring.

- You can pass a ``query`` to the ``find_in_search_results`` method, which will rerank and return **top_k** results based on the query.

.. code:: python

    from nosible import Nosible

    # Simple search with just date.
    with Nosible() as nos:
        results = nos.search(
            question="Hedge funds seek to expand into private credit", n_results=100, publish_start="2024-06-01"
        )

    for idx, result in enumerate(results):
        print(f"{idx:2}: {result.similarity:.2f} | {result.title} - {result.url}")

    # Find top 5 results related to Warren Buffett
    new = results.find_in_search_results("Warren Buffett", top_k=5)

    print(new)

--------------

📡 Swagger Docs
~~~~~~~~~~~~~~~

You can find online endpoints to the NOSIBLE Search API Swagger Docs
`here <https://www.nosible.ai/search/v1/docs/swagger#/>`__.

--------------
