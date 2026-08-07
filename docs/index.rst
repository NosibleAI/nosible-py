.. image:: _static/readme.png
   :alt: NOSIBLE
   :class: top-logo

NOSIBLE Python SDK
==================

The NOSIBLE Python SDK provides synchronous access to Search API v2.1 and the
NOSIBLE World API from one client.

Installation
------------

.. code-block:: bash

   pip install "nosible==0.4.0"

Python 3.9 and newer are supported.

Authentication
--------------

Create an API key in the `NOSIBLE application <https://app.nosible.com/>`_,
then set ``NOSIBLE_API_KEY``:

.. code-block:: powershell

   $Env:NOSIBLE_API_KEY="nos_sk_..."

.. code-block:: bash

   export NOSIBLE_API_KEY="nos_sk_..."

Search requests use the ``api-key`` header. Authenticated World requests use
``Authorization: Bearer``. World version is always credential-free. Search
Schema and Markdown delivery requests are public-first and retry once with
SDK-managed bearer authentication only when a deployment rejects anonymous
access and an API key is configured.

First Search
------------

.. code-block:: python

   from nosible import Nosible

   with Nosible() as client:
       results = client.fast_search(
           question="What is changing in semiconductor capacity?",
           n_results=25
       )

       for result in results:
           print(result.title, result.similarity)

First World query
-----------------

.. code-block:: python

   from nosible import Nosible

   with Nosible() as client:
       dates = client.world.dates()
       events = client.world.events(date=dates["dates"][0])

       for event in events:
           print(event.event_id, event.event.get("title"))

The combined endpoint documentation is available at
`docs.nosible.com <https://docs.nosible.com/>`_.

.. toctree::
   :maxdepth: 4
   :caption: User Guide
   :hidden:

   Getting Started <self>
   search_v2_1
   world
   errors
   configuration
   releasing
   examples
   mcp_server

API reference
-------------

.. autosummary::
   :toctree: api
   :caption: API Reference

   nosible.Nosible
   nosible.Result
   nosible.ResultSet
   nosible.RichResult
   nosible.Search
   nosible.SearchSet
   nosible.WebPageData
   nosible.Snippet
   nosible.SnippetSet
   nosible.WorldClient
   nosible.WorldEvent
   nosible.WorldEventPage
