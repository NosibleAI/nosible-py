Rate Limits
-----------

This python package implements automatic rate limiting, searches will be delayed until your rate limit is no longer
throttling. Below are the throttling rules by plan, to upgrade your plan, visit our
`products page <https://www.nosible.ai/products>`_:

- Excluding Searches for the Business+ and Enterprise plans, all packages are subject to a 60
  requests per minute limit.

- Unless otherwise indicated, bulk searches are limited to one-at-a-time per API key.


+----------------+---------------+---------------+------------+--------------+---------------+
| Plan           | Searches      | Bulk Searches | URL Visits | Subscription | Effective CPM |
+================+===============+===============+============+==============+===============+
| **Free**       | 3000          | 300           | 300        | $–           | $4.00         |
+----------------+---------------+---------------+------------+--------------+---------------+
| **Basic**      | 14 000        | 1400          | 1400       | $49.00       | $3.50         |
+----------------+---------------+---------------+------------+--------------+---------------+
| **Pro**        | 67 000        | 6700          | 6700       | $199.00      | $3.00         |
+----------------+---------------+---------------+------------+--------------+---------------+
| **Pro+**       | 320 000       | 32 000        | 32000      | $799.00      | $2.50         |
+----------------+---------------+---------------+------------+--------------+---------------+
| **Business**   | 2 000 000     | 200 000       | 200000     | $3,999.00    | $2.00         |
+----------------+---------------+---------------+------------+--------------+---------------+
| **Business+**  | 5 000 000     | 500 000       | 500000     | $7,499.00    | $1.50         |
+----------------+---------------+---------------+------------+--------------+---------------+
| **Enterprise** | 15 000 000    | 1 500 000     | 1500000    | $14,999.00   | $1.00         |
+----------------+---------------+---------------+------------+--------------+---------------+

All endpoints are automatically throttled. Call ``.get_ratelimits()`` at runtime to inspect your allowances.
