Configuration
=============

Client configuration
--------------------

``Nosible`` reads ``NOSIBLE_API_KEY`` and ``LLM_API_KEY`` when the equivalent
constructor arguments are omitted. ``base_url`` defaults to the merged
``https://nosible.world/api`` origin. ``timeout`` applies to HTTP requests and
``retries`` is the maximum number of transport attempts.

An injected ``httpx.Client`` remains owned by the caller:

.. code-block:: python

   import httpx

   from nosible import Nosible

   http = httpx.Client()
   client = Nosible(
       nosible_api_key="nos_sk_...",
       base_url="https://staging.example/api",
       http_client=http,
       retries=3,
       timeout=30
   )
   client.close()
   http.close()

Authentication routing
----------------------

Search routes use the ``api-key`` header, while authenticated World routes use
``Authorization: Bearer``. World version is public and always credential-free.
Search Schema and Markdown delivery requests are sent without credentials
first. If a deployment responds with an authentication error, the SDK retries
once with SDK-managed bearer authentication when an API key is configured.
Authentication configured on an injected ``httpx.Client`` is replaced for
every SDK request. Presigned Bulk and Time Search downloads are always
credential-free.

Search defaults
---------------

Fast Search keeps the established SDK defaults of ``n_results=100``,
``n_probes=30``, and ``n_contextify=128``. These intentionally differ from the
service schema defaults of 10 results and 256 context tokens. Calls requesting
one through nine Fast results request the service minimum of ten and truncate
the returned ``ResultSet`` locally.

Rich Search defaults to 10 results and 256 context tokens. Bulk Search defaults
to 1,000 results and Time Search defaults to 25 results per interval.

Common Search fields include:

.. list-table::
   :header-rows: 1

   * - Field
     - Constraint
   * - ``question`` and ``instruction``
     - 1 to 500 characters when supplied.
   * - ``expansions``
     - At most 10 strings.
   * - ``must_include`` and ``must_exclude``
     - At most 100 strings each.
   * - ``companies``
     - At most 3 company names.
   * - ``collection``
     - ``everything`` or ``this-week``.
   * - ``algorithm``
     - ``string``, ``lexical``, ``baseline``, ``hamming``, ``hybrid-1``,
       ``hybrid-2``, ``hybrid-3``, or ``company``.
   * - ``min_similarity``
     - 0 through 1 inclusive.
   * - ``brand_safety``
     - ``Safe``, ``Sensitive``, or ``Unsafe``.
   * - ``language``
     - Supported lowercase ISO 639-1 code.
   * - ``continent``
     - NOSIBLE continent name.

Bulk and Time downloads
-----------------------

``poll_interval`` controls how frequently the client checks a presigned result
URL. ``poll_timeout`` limits the total wait. Credentials are never forwarded
to that URL, including authentication policies configured on an injected
``httpx.Client``. Transient HTTP statuses use the configured retry count while
404 remains the signal that a Search job is still pending. The downloaded
bytes are decrypted with Fernet and decompressed as Zstandard or legacy gzip.

Retry policy
------------

Connection and transport errors use the configured attempt count. HTTP 429,
500, 502, 503, and 504 responses are retried only for safe read methods
(``GET``, ``HEAD``, and ``OPTIONS``), preventing automatic replay of Search
POST requests. Numeric and HTTP-date ``Retry-After`` values are honored.

LLM configuration
-----------------

``openai_base_url``, ``expansions_model``, and ``sentiment_model`` configure
the optional OpenAI-compatible LLM operations. The LLM key is not used for
Search or World requests.
