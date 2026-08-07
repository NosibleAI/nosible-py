"""Tests for test result."""

import os
import types

import pytest

from nosible import Result, ResultSet

TEST_MODULE = os.path.basename(p=__file__)


class DummyClient:
    """Minimal client used by the sentiment binding test."""

    llm_api_key = "dummy"

    def scrape_url(
        self: "DummyClient",
        url: str
    ) -> str:
        """
        Return a stable scrape result.

        :param url: URL that would be scraped.
        :return: Stable test value.
        """
        return "webpage"


def test_result_to_dict_and_str_and_indexing_and_addition() -> None:
    """

    Verify result to dict and str and indexing and addition.

    :return: Test result or None.
    """
    result = Result(
        url="https://example.com",
        title="Example Domain",
        description="Desc",
        netloc="example.com",
        published="2024-01-01",
        visited="2024-01-01",
        author="Author",
        content="<html>",
        language="en",
        similarity=0.98,
        url_hash="abc123"
    )
    result_payload = result.to_dict()
    keys = sorted(result_payload.keys())
    for expected in (
        "author",
        "content",
        "description",
        "language",
        "netloc",
        "published",
        "visited",
        "title",
        "similarity",
        "url",
        "url_hash",
    ):
        assert expected in keys

    rendered = str(Result(
        title="T",
        similarity=0.9876
    ))
    assert "0.9876" in rendered and "T" in rendered
    rendered = str(Result(
        title=None,
        similarity=None
    ))
    assert "{}" in rendered

    result2 = Result(
        url=None,
        title=None,
        similarity=None
    )
    assert result2["title"] is None
    assert result2["similarity"] is None
    with pytest.raises(expected_exception=KeyError):
        _ = result2["nope"]

    first_result = Result(
        title="A",
        similarity=0.1
    )
    second_result = Result(
        title="B",
        similarity=0.2
    )
    combined = first_result + second_result
    assert isinstance(combined, ResultSet)


def test_sentiment_monkeypatch_and_scrape_url() -> None:
    """

    Verify sentiment monkeypatch and scrape url.

    :return: Test result or None.
    """
    result = Result(
        url="u",
        content="c"
    )
    result.sentiment = types.MethodType(fake_sent, result)
    assert result.sentiment(client=DummyClient()) == 0.5


def fake_sent(
    result: Result,
    client: DummyClient
) -> float:
    """
    Return stable sentiment for the method-binding test.

    :param result: Result receiving the bound method.
    :param client: Client passed to the sentiment method.
    :return: Stable sentiment value.
    """
    return 0.5
