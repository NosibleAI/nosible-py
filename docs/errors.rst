Errors and transport
====================

API failures raise a stable ``NosibleAPIError`` hierarchy. The base exception
inherits from ``ValueError`` for compatibility with existing applications.

.. code-block:: python

   from nosible import Nosible, RateLimitError

   try:
       Nosible().get_limits()
   except RateLimitError as error:
       print(error.retry_after)

All API errors expose ``status_code``, ``code``, ``method``, ``path``,
``body``, and ``retry_after``.

Exception hierarchy
-------------------

.. currentmodule:: nosible

.. autoclass:: NosibleAPIError
   :members:

.. autoclass:: AuthenticationError

.. autoclass:: ValidationError

.. autoclass:: RateLimitError

.. autoclass:: ConflictError

.. autoclass:: GoneError

.. autoclass:: CursorExpiredError

.. autoclass:: AccessDeniedError

.. autoclass:: NotFoundError

.. autoclass:: BackendError

Retry behavior
--------------

Transport failures are retried up to the configured attempt count. HTTP 429,
500, 502, 503, and 504 responses are retried only for safe read requests,
which avoids duplicating POST mutations or Search jobs. The client honors both
numeric and HTTP-date ``Retry-After`` headers.

Presigned Bulk and Time download GETs follow the same retry policy for
transient statuses. A 404 is returned to the polling layer rather than retried
by the transport because it means the asynchronous result is not ready yet.

Pass ``base_url`` to target another merged API origin and ``http_client`` to
inject an ``httpx.Client``. The caller retains ownership of an injected
client. Client-level authentication is disabled for presigned download
requests.
