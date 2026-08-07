"""Controlled live smoke tests for deployed Search and World contracts."""

import os

import pytest

from nosible import Nosible

TEST_MODULE = os.path.basename(p=__file__)

pytestmark = pytest.mark.integration


def test_live_public_world_discovery() -> None:
    """
    Verify deployed public-first World discovery routes.

    :return: None.
    """
    require_live_key()
    with Nosible() as client:
        version = client.world.version()
        schema = client.world.search_schema()
        markdown = client.world.markdown_today(top=1)

    assert isinstance(version, dict)
    assert isinstance(schema, dict)
    assert isinstance(markdown, str)


def test_live_authenticated_search_and_world_inventory() -> None:
    """
    Verify deployed authenticated Search and World discovery contracts.

    :return: None.
    """
    require_live_key()
    with Nosible() as client:
        limits = client.get_limits()
        dates = client.world.dates()

    assert isinstance(limits, dict)
    assert isinstance(dates, dict)
    assert dates.get("dates")


def require_live_key() -> None:
    """
    Require a configured key for an authenticated live smoke test.

    :return: None.
    """
    if not os.getenv(key="NOSIBLE_API_KEY"):
        pytest.fail(reason="NOSIBLE_API_KEY is required for the live contract job")
