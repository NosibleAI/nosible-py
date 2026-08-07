"""Public Python contracts for the NOSIBLE Search + World release."""

import os
import inspect
from typing import Any

import httpx
import pytest

import nosible

TEST_MODULE = os.path.basename(p=__file__)


pytestmark = pytest.mark.contract


class RecordingEmptyHandler:
    """Return empty responses while recording requests."""

    def __init__(
        self: "RecordingEmptyHandler"
    ) -> None:
        """
        Initialize an empty request log.

        :return: None.
        """
        self.requests: list[httpx.Request] = []

    def __call__(
        self: "RecordingEmptyHandler",
        request: httpx.Request
    ) -> httpx.Response:
        """
        Record a request and return an empty response.

        :param request: Request received by the mock transport.
        :return: Empty successful HTTP response.
        """
        self.requests.append(request)
        return httpx.Response(
            status_code=200,
            json={},
            request=request
        )


def test_public_version_identifies_the_release() -> None:
    """

    Verify public version identifies the release.

    :return: Test result or None.
    """
    assert nosible.__version__ == "0.4.0"


def test_public_exports_are_additive() -> None:
    """

    Verify public exports are additive.

    :return: Test result or None.
    """
    expected = {
        "Nosible",
        "Result",
        "ResultSet",
        "Search",
        "SearchSet",
        "Snippet",
        "SnippetSet",
        "WebPageData",
        "RichResult",
        "WorldClient",
        "WorldEvent",
        "WorldEventPage",
        "NosibleAPIError",
        "AuthenticationError",
        "ValidationError",
        "RateLimitError",
        "ConflictError",
        "CursorExpiredError",
        "AccessDeniedError",
        "NotFoundError",
        "BackendError",
    }

    assert expected <= set(nosible.__all__)
    for name in expected:
        assert getattr(nosible, name) is not None


def test_nosible_constructor_supports_transport_injection_without_io(
    client_factory: Any
) -> None:
    """

    Verify nosible constructor supports transport injection without io.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    assert recorder.requests == []
    assert client.world is not None


def test_nosible_constructor_keeps_existing_keyword_parameters() -> None:
    """

    Verify nosible constructor keeps existing keyword parameters.

    :return: Test result or None.
    """
    parameters = inspect.signature(obj=nosible.Nosible).parameters

    assert "nosible_api_key" in parameters
    assert "llm_api_key" in parameters
    assert "base_url" in parameters
    assert "http_client" in parameters


def test_default_api_key_still_comes_from_environment(
    monkeypatch: Any
) -> None:
    """

    Verify default api key still comes from environment.

    :param monkeypatch: Test dependency or input.
    :return: Test result or None.
    """
    monkeypatch.setenv(
        name="NOSIBLE_API_KEY",
        value="nos_from_environment"
    )
    handler = RecordingEmptyHandler()
    http_client = httpx.Client(transport=httpx.MockTransport(handler=handler))
    client = None
    try:
        client = nosible.Nosible(http_client=http_client)

        assert handler.requests == []
        assert client.world is not None
    finally:
        if client is not None:
            client.close()
        http_client.close()


def test_injected_http_client_is_not_owned_by_nosible(
    client_factory: Any
) -> None:
    """

    Verify injected http client is not owned by nosible.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory()

    client.close()

    assert recorder.http_client.is_closed is False


def test_search_model_adds_v2_1_fields_and_round_trips() -> None:
    """

    Verify search model adds v2 1 fields and round trips.

    :return: Test result or None.
    """
    search = nosible.Search(
        question="semiconductor investment",
        companies=["NVIDIA", "TSMC"],
        collection="this-week",
        deduplicate=True
    )

    payload = search.to_dict()
    restored = nosible.Search.from_dict(data=payload)

    assert payload["companies"] == ["NVIDIA", "TSMC"]
    assert payload["collection"] == "this-week"
    assert payload["deduplicate"] is True
    assert restored == search


def test_search_model_keeps_legacy_fields() -> None:
    """

    Verify search model keeps legacy fields.

    :return: Test result or None.
    """
    search = nosible.Search(
        question="private credit",
        publish_start="2026-01-01",
        include_netlocs=["example.com"],
        include_companies=["/m/012345"],
        certain=True
    )

    assert search.to_dict()["publish_start"] == "2026-01-01"
    assert search.to_dict()["include_netlocs"] == ["example.com"]
    assert search.to_dict()["include_companies"] == ["/m/012345"]
    assert search.to_dict()["certain"] is True
