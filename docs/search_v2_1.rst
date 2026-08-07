Search API v2.1
===============

Search calls use the merged API origin and the ``api-key`` header.

Interactive Search
------------------

``fast_search`` returns legacy-compatible ``Result`` objects while preserving
the complete Search v2.1 response. ``rich_search`` returns ``RichResult``
objects and preserves each selected enrichment block.

.. code-block:: python

   from nosible import Nosible

   with Nosible() as client:
       results = client.fast_search(
           question="What is changing in semiconductor capacity?",
           companies=["NVIDIA", "TSMC"],
           collection="this-week",
           deduplicate=True,
           n_results=25
       )

       rich = client.rich_search(
           question="What is changing in semiconductor capacity?",
           n_results=10,
           enrich_vectors=False
       )

Fast Search retains the SDK's established defaults of 100 results and 128
context tokens, even though the service schema defaults are 10 and 256.
Requests below the service minimum of 10 are truncated locally.

Scrape responses use lossless ``Snippet`` models. Unknown fields, omitted
known fields, and explicitly null known fields retain their original wire
representation during ``from_dict`` / ``to_dict`` round trips.

Asynchronous Search
-------------------

``bulk_search`` and ``time_search`` submit a task, poll the presigned result
URL, decrypt the Fernet payload, and decompress current Zstandard or legacy
gzip data. Authentication headers, including client-level authentication on
an injected ``httpx.Client``, are never sent to the download host. Transient
download responses use the configured retry policy.

.. code-block:: python

   buckets = client.time_search(
       question="semiconductor investment",
       start="2026-01-01T00:00:00Z",
       end="2026-04-01T00:00:00Z",
       frequency="1w",
       n_results=100
   )

Time Search composes the common Search schema with its time fields. It permits
at most 500 intervals and 50,000 requested results per call. ``time_search``
preserves the downloaded interval envelope; ``bulk_search`` returns a
``ResultSet``.

Endpoint coverage
-----------------

The SDK covers all Search v2.1 routes:

.. list-table::
   :header-rows: 1

   * - Method
     - Purpose
   * - ``search``
     - Cybernaut agentic Search.
   * - ``fast_search``
     - Interactive ranked Search.
   * - ``rich_search``
     - Interactive enriched Search.
   * - ``bulk_search``
     - Long-running high-volume Search.
   * - ``time_search``
     - Independent searches across time intervals.
   * - ``scrape_url``
     - Structured page and snippet extraction.
   * - ``topic_trend``
     - Date-keyed topic prevalence.
   * - ``save_search``
     - Create or update a saved Search.
   * - ``get_searches``
     - List saved Searches.
   * - ``delete_search``
     - Delete a saved Search.
   * - ``get_limits``
     - Retrieve current key limits.

``fast_searches`` is the SDK batch convenience for issuing several Fast
Search requests. Question lists, ``list[Search]``, and ``SearchSet`` inputs
all receive the shared filters and retrieval options supplied to the batch;
non-null fields populated on an individual ``Search`` model retain precedence.
This includes ``False`` for the optional ``certain`` filter. Expansion
generation is enabled when either the batch or the individual model opts in.
Requests run concurrently up to the client's configured ``concurrency`` while
results retain input order.
