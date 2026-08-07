Releasing
=========

Release metadata
----------------

The version in ``pyproject.toml``, ``nosible.__version__``, and
``docs/conf.py`` must match. A publishing tag must be exactly that version
prefixed with ``v``. For example, package version ``0.4.0`` may only be
published from tag ``v0.4.0``.

The CI build validates this relationship before creating distributions. A tag
such as ``v0.4.1`` cannot publish artifacts that identify themselves as
``0.4.0``.

Local release checks
--------------------

Run the same offline checks before creating a release tag:

.. code-block:: powershell

   python scripts/check_release.py
   python scripts/check_python_rules.py
   python -m ruff check .
   python -m pytest
   python -m sphinx -W --keep-going -E -b html docs docs/_build/html
   python -m build

The GitHub workflow repeats the test matrix on Linux, macOS, and Windows,
using every advertised Python version: 3.9, 3.10, 3.11, 3.12, and 3.13. It
verifies a no-isolation build with the declared minimum
``setuptools==75.1.0``, builds both the wheel and source distribution,
validates them with Twine, and publishes only after every prerequisite
succeeds.

A scheduled or manually dispatched workflow also runs the opt-in live Search
and World contract suite. It requires the repository's ``NOSIBLE_API_KEY``
secret and fails instead of silently skipping when the secret is absent. PyPI
authentication uses trusted publishing; no long-lived upload token is stored
in the workflow.
