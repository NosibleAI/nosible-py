Rate Limits
-----------

This python package implements automatic rate limiting, searches will be delayed until your rate limit is no longer
throttling. Below are the throttling rules by plan, to upgrade your plan, visit our
`products page <https://www.nosible.ai/products>`_:

Free
^^^^

- **Cost**: $0
- **CPM**: $0

+---------------+-----------+---------+------------+
| Endpoint      | Per Month | Per Day | Per Minute |
+===============+===========+=========+============+
| Search        |  100      | 10      | 10         |
+---------------+-----------+---------+------------+
| URL Visits    | 300       | 10      | 1          |
+---------------+-----------+---------+------------+
| Bulk Search   | 300       | 10      | 1          |
+---------------+-----------+---------+------------+


Basic
^^^^^

- **Cost**: $120
- **CPM**: $4

+---------------+-----------+---------+------------+
| Endpoint      | Per Month | Per Day | Per Minute |
+===============+===========+=========+============+
| Search        | 30,000    | 1,000   | 10         |
+---------------+-----------+---------+------------+
| URL Visits    | 3,000     | 100     | 1          |
+---------------+-----------+---------+------------+
| Bulk Search   | 3,000     | 100     | 1          |
+---------------+-----------+---------+------------+

Pro
^^^

- **Cost**: $450
- **CPM**: $3

+---------------+------------+---------+------------+
| Endpoint      | Per Month  | Per Day | Per Minute |
+===============+============+=========+============+
| Search        | 150,000    | 5,000   | 10         |
+---------------+------------+---------+------------+
| URL Visits    | 7,500      | 250     | 1          |
+---------------+------------+---------+------------+
| Bulk Search   | 7,500      | 250     | 1          |
+---------------+------------+---------+------------+

Pro+
^^^^^

- **Cost**: $750
- **CPM**: $2.5

+---------------+------------+---------+------------+
| Endpoint      | Per Month  | Per Day | Per Minute |
+===============+============+=========+============+
| Search        | 300,000    | 10,000  | 10         |
+---------------+------------+---------+------------+
| URL Visits    | 15,000     | 500     | 2          |
+---------------+------------+---------+------------+
| Bulk Search   | 15,000     | 500     | 2          |
+---------------+------------+---------+------------+

Business
^^^^^^^^

- **Cost**: $3,000
- **CPM**: $0.002

+---------------+-------------+---------+------------+
| Endpoint      | Per Month   | Per Day | Per Minute |
+===============+=============+=========+============+
| Search        | 1,500,000   | 50,000  | 3          |
+---------------+-------------+---------+------------+
| URL Visits    | 30,000      | 1,000   | 2          |
+---------------+-------------+---------+------------+
| Bulk Search   | 30,000      | 1,000   | 2          |
+---------------+-------------+---------+------------+

Business+
^^^^^^^^^

- **Cost**: $4,500
- **CPM**: $0.0015

+---------------+-------------+---------+-------------+
| Endpoint      | Per Month   | Per Day | Per Minute  |
+===============+=============+=========+=============+
| Search        | 3,000,000   | 100,000 | 100         |
+---------------+-------------+---------+-------------+
| URL Visits    | 60,000      | 2,000   | 3           |
+---------------+-------------+---------+-------------+
| Bulk Search   | 60,000      | 2,000   | 3           |
+---------------+-------------+---------+-------------+

Enterprise
^^^^^^^^^^

- **Cost**: $15,000.00
- **CPM**: $0.001

+---------------+--------------+---------+-------------+
| Endpoint      | Per Month    | Per Day | Per Minute  |
+===============+==============+=========+=============+
| Search        | 15,000,000   | 500,000 | 400         |
+---------------+--------------+---------+-------------+
| URL Visits    | 150,000      | 5,000   | 5           |
+---------------+--------------+---------+-------------+
| Bulk Search   | 150,000      | 5,000   | 5           |
+---------------+--------------+---------+-------------+

All endpoints are automatically throttled. Call ``.get_ratelimits()`` at runtime to inspect your allowances.
