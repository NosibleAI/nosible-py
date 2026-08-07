"""Shared fixtures for opt-in live integration tests."""

import os
from typing import Any, List

import pytest

from nosible import Nosible, Search, SearchSet

TEST_MODULE = os.path.basename(p=__file__)


INTEGRATION_FIXTURES = frozenset(
    {
        "bulk_search_data",
        "scrape_url_data",
        "search_data",
        "searches_data",
        "snippets_data",
        "topic_trend_data"
    }
)
INTEGRATION_TEST_NAMES = frozenset(
    {
        "test_similar_excludes_current_document"
    }
)


def pytest_addoption(
    parser: Any
) -> None:
    """
    Register the explicit live-integration test switch.

    :param parser: Pytest command-line option parser.
    :return: None.
    """
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run tests that call the live NOSIBLE APIs."
    )


def pytest_configure(
    config: pytest.Config
) -> None:
    """
    Register the integration marker for strict marker validation.

    :param config: Active pytest configuration.
    :return: None.
    """
    config.addinivalue_line(
        name="markers",
        line="integration: requires live NOSIBLE credentials and network access"
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: List[pytest.Item]
) -> None:
    """
    Skip live tests unless the caller explicitly opts in.

    :param config: Active pytest configuration.
    :param items: Collected pytest items.
    :return: None.
    """
    run_integration = config.getoption(
        name="--run-integration"
    )
    skip_marker = pytest.mark.skip(
        reason="live integration test; pass --run-integration to enable"
    )
    for item in items:
        uses_live_fixture = bool(
            INTEGRATION_FIXTURES.intersection(item.fixturenames)
        )
        is_integration = (
            uses_live_fixture
            or item.name in INTEGRATION_TEST_NAMES
            or item.get_closest_marker(name="integration") is not None
        )
        if not is_integration:
            continue
        item.add_marker(
            marker=pytest.mark.integration
        )
        if not run_integration:
            item.add_marker(
                marker=skip_marker
            )


@pytest.fixture(scope="session")
def search_data() -> Any:
    """
    Fetch one live Fast Search result set.

    :return: Live Fast Search result set.
    """
    require_integration_key()
    with Nosible() as client:
        return client.fast_search(
            question="Hedge funds seek to expand into private credit",
            n_results=10
        )


@pytest.fixture(scope="session")
def snippets_data(
    scrape_url_data: Any
) -> Any:
    """
    Return snippets from the live Scrape fixture.

    :param scrape_url_data: Live scraped page data.
    :return: Snippet collection from the scraped page.
    """
    return scrape_url_data.snippets


@pytest.fixture(scope="session")
def searches_data() -> Any:
    """
    Fetch two live concurrent Fast Search result sets.

    :return: List of live Fast Search result sets.
    """
    require_integration_key()
    searches = SearchSet(
        searches_list=[
            Search(
                question="Hedge funds seek to expand into private credit",
                n_results=5
            ),
            Search(
                question="How have the Trump tariffs impacted the US economy?",
                n_results=5
            )
        ]
    )
    with Nosible() as client:
        return list(
            client.fast_searches(
                searches=searches
            )
        )


@pytest.fixture(scope="session")
def scrape_url_data(
    search_data: Any
) -> Any:
    """
    Scrape the second live search result.

    :param search_data: Live Fast Search result set.
    :return: Scraped web-page data.
    """
    require_integration_key()
    with Nosible() as client:
        return search_data[1].scrape_url(
            client=client
        )


@pytest.fixture(scope="session")
def bulk_search_data() -> Any:
    """
    Fetch one live Bulk Search result set.

    :return: Live Bulk Search result set.
    """
    require_integration_key()
    with Nosible() as client:
        return client.bulk_search(
            question="Hedge funds seek to expand into private credit",
            n_results=1000
        )


@pytest.fixture(scope="session")
def topic_trend_data() -> Any:
    """
    Fetch one live Topic Trend response.

    :return: Live Topic Trend response.
    """
    require_integration_key()
    with Nosible() as client:
        return client.topic_trend(
            query="Christmas shopping"
        )


def require_integration_key() -> None:
    """
    Require a NOSIBLE key before a live fixture can execute.

    :return: None.
    """
    if not os.getenv(
        key="NOSIBLE_API_KEY"
    ):
        pytest.skip(
            reason="NOSIBLE_API_KEY is required for live integration tests"
        )
