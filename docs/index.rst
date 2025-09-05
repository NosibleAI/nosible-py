.. image:: _static/readme.png
   :alt: Nosible logo
   :class: top-logo

NOSIBLE Search Client
======================

Welcome to the NOSIBLE Client package! This documentation will give you an in-depth overview of the NOSIBLE
Search API, and show you how to harness the power of the NOSIBLE Search Engine.

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

1. Sign in to `NOSIBLE <https://www.nosible.ai/search-api>`_ and grab your free API key.
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

🔍 Your first search
~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from nosible import Nosible

    with Nosible(nosible_api_key="YOUR API KEY") as client:

        results = client.fast_search(
            question="What is Artificial General Intelligence?"
        )

        print(results)

--------------

⚒️ Examples and Demos
~~~~~~~~~~~~~~~~~~~~~

To easily view examples of how to use the client package, or demos to see what can be achieved with the NOSIBLE
search engine, view our `examples and demos page <https://nosible-py.readthedocs.io/en/latest/examples.html>`__.

📡 Swagger Docs
~~~~~~~~~~~~~~~

You can find online endpoints to the NOSIBLE Search API Swagger Docs
`here <https://www.nosible.ai/search/v2/docs/#/>`__.

--------------

.. toctree::
   :maxdepth: 4
   :caption: User Guide
   :hidden:

   Getting Started <self>
   configuration
   examples
   rate_limits
   mcp_server

API reference
-------------

.. autosummary::
   :toctree: api
   :caption: API Reference

   nosible.Nosible
   nosible.Result
   nosible.ResultSet
   nosible.Search
   nosible.SearchSet
   nosible.WebPageData
   nosible.Snippet
   nosible.SnippetSet