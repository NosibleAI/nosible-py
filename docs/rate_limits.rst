Rate Limits
-----------

This python package implements automatic rate limiting, searches will be delayed until your rate limit is no longer
throttling. Below are the throttling rules by plan, to upgrade your plan, visit our
`products page <https://www.nosible.ai/products>`_:

- Excluding Fast Searches for the Startup and Business tier, all packages are subject to a 60
  requests per minute limit.

- Unless otherwise indicated, bulk searches are limited to one-at-a-time per API key.


+----------------+---------------+---------------+------------+--------------+---------------+
| Plan           | Fast Searches | Bulk Searches | URL Scrapes| Subscription | Effective CPM |
+================+===============+===============+============+==============+===============+
| **Free**       | 3000          | 300           | 300        | $-           | $1.50         |
+----------------+---------------+---------------+------------+--------------+---------------+
| **Consumer**   | 30 000        | 3000          | 3000       | $45.00       | $1.00         |
+----------------+---------------+---------------+------------+--------------+---------------+
| **Startup**    | 300 000       | 30 000        | 30 000     | $300.00      | $1.00         |
+----------------+---------------+---------------+------------+--------------+---------------+
| **Business**   | 3 000 000     | 300 000       | 300 000    | $1,500.00    | $0.50         |
+----------------+---------------+---------------+------------+--------------+---------------+


All endpoints are automatically throttled. Call ``.get_ratelimits()`` at runtime to inspect your allowances.
