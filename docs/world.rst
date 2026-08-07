NOSIBLE World
=============

World is available through ``client.world``. Version is public and always
credential-free. Search Schema and Markdown delivery routes are public-first;
the SDK retries an authentication failure once with SDK-managed bearer
authentication when an API key is configured. The remaining World routes use
bearer authentication automatically.

.. code-block:: python

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
           limit=10,
           include_live=False,
           include_thread=True,
           floor=0.35
       )

Models
------

``WorldEventPage`` is iterable and indexable while retaining pagination,
facets, timing, hydration misses, and ``as_of`` metadata. ``WorldEvent`` and
``WorldEventPage`` preserve unknown fields so newer server schemas can be
round-tripped without loss. Lite projections do not invent omitted fields.

Endpoint coverage
-----------------

The World namespace covers every route in the current endpoint inventory:

.. list-table::
   :header-rows: 1

   * - Methods
     - Routes
   * - ``events``, ``day_search``, ``snapshot``
     - Dated event list, structured day Search, and snapshot.
   * - ``event``, ``similar_events``, ``event_aggregates``, ``coverage``
     - Event detail, neighbors, aggregate metadata, and source evidence.
   * - ``entity_events``, ``ticker_events``, ``ontology_events``
     - Cursor-based World timelines.
   * - ``search``, ``aggregate``
     - Global World Search and analytics.
   * - ``autocomplete``, ``semantic_search``
     - Dated autocomplete and semantic retrieval.
   * - ``resolve``, ``entity_summary``, ``ticker``
     - Entity and security metadata.
   * - ``version``, ``dates``, ``search_schema``
     - Service and archive metadata.
   * - ``markdown_index``, ``markdown_today``, ``markdown_yesterday``
     - Daily Markdown indexes.
   * - ``markdown_resolve``, ``markdown_entity``, ``markdown_ticker``
     - Markdown discovery and dossiers.
   * - ``markdown_event``, ``markdown_bulk``
     - Event Markdown and bulk ZIP delivery.

``entity_summary`` is an all-time summary and accepts only entity ``type`` and
``name``. ``dates`` returns the currently accessible archive directory and
does not accept a date window.

``similar_events`` accepts ``floor`` as the minimum similarity threshold for
HNSW neighbors, in addition to ``limit``, ``include_live``, and
``include_thread``.

``search_schema`` and every ``markdown_*`` method use the public-first policy
described above. The first request is credential-free. If the deployment
rejects anonymous access and the client has a key, the SDK retries once with
SDK-managed bearer authentication.

Use ``include="event_lite"`` for compact timeline events or
``include="event_full"`` for complete World payloads.
