"""Stable exception contracts shared by Search and World requests."""

import os
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from typing import Any

import httpx
import pytest

import nosible

TEST_MODULE = os.path.basename(p=__file__)


pytestmark = pytest.mark.contract


class TransientTransportHandler:
    """Fail once before returning a stable successful response."""

    def __init__(
        self: "TransientTransportHandler"
    ) -> None:
        """
        Initialize the request-attempt log.

        :return: None.
        """
        self.attempts: list[httpx.Request] = []

    def __call__(
        self: "TransientTransportHandler",
        request: httpx.Request
    ) -> httpx.Response:
        """
        Fail the first request and satisfy the second.

        :param request: Request received by the mock transport.
        :return: Successful dates response after the first attempt.
        """
        self.attempts.append(request)
        if len(self.attempts) == 1:
            raise httpx.ConnectError(
                message="temporary connection failure",
                request=request
            )
        return httpx.Response(
            status_code=200,
            json={"dates": ["2026-07-20"]},
            request=request
        )


class DownloadTransportHandler:
    """Record download attempts and return a configured status sequence."""

    def __init__(
        self: "DownloadTransportHandler",
        status_codes: list[int]
    ) -> None:
        """
        Initialize the download response sequence.

        :param status_codes: HTTP statuses returned in attempt order.
        :return: None.
        """
        self.requests: list[httpx.Request] = []
        self.status_codes = status_codes

    def __call__(
        self: "DownloadTransportHandler",
        request: httpx.Request
    ) -> httpx.Response:
        """
        Record one request and return its configured response.

        :param request: Presigned download request.
        :return: Configured download response.
        """
        self.requests.append(request)
        status_code = self.status_codes.pop(0)
        return httpx.Response(
            status_code=status_code,
            content=b"downloaded" if status_code == 200 else b"retry",
            headers={"Retry-After": "0"} if status_code == 503 else None,
            request=request
        )


class ClientBearerAuth(httpx.Auth):
    """Inject a bearer credential through an HTTPX client auth policy."""

    def auth_flow(
        self: "ClientBearerAuth",
        request: httpx.Request
    ) -> Iterator[httpx.Request]:
        """
        Add the credential normally applied by the injected HTTPX client.

        :param request: Outbound HTTP request.
        :return: Iterator yielding the authenticated request.
        """
        request.headers["Authorization"] = "Bearer injected-client-secret"
        yield request


@pytest.mark.parametrize(
    argnames=("status", "body", "error_name"),
    argvalues=[
        (
            400,
            {"error": "invalid_date", "message": "Use YYYY-MM-DD."},
            "ValidationError",
        ),
        (
            401,
            {"error": "invalid_api_key", "message": "Invalid API key."},
            "AuthenticationError",
        ),
        (
            403,
            {
                "error": "access_denied",
                "message": "The date is outside this tier.",
                "tier_required": "world_pro",
            },
            "AccessDeniedError",
        ),
        (
            404,
            {"error": "not_found", "message": "No data for this date."},
            "NotFoundError",
        ),
        (
            409,
            {"error": "conflict", "message": "The resource changed."},
            "ConflictError",
        ),
        (
            410,
            {
                "error": "cursor_expired",
                "message": "The index was rebuilt; restart pagination.",
            },
            "CursorExpiredError",
        ),
        (
            422,
            {
                "error": "validation_error",
                "detail": [{"loc": ["body", "limit"], "msg": "invalid"}],
            },
            "ValidationError",
        ),
        (
            500,
            {"error": "backend_unreachable", "message": "Backend failed."},
            "BackendError",
        ),
        (
            501,
            {"error": "not_implemented", "message": "Not implemented."},
            "BackendError",
        ),
        (
            502,
            {"error": "bad_gateway", "message": "Upstream failed."},
            "BackendError",
        ),
        (
            503,
            {"error": "unavailable", "message": "Temporarily unavailable."},
            "BackendError",
        ),
        (
            504,
            {"error": "gateway_timeout", "message": "Upstream timed out."},
            "BackendError",
        ),
    ]
)
def test_http_statuses_raise_stable_typed_errors(
    client_factory: Any,
    status: Any,
    body: Any,
    error_name: Any
) -> None:
    """

    Verify http statuses raise stable typed errors.

    :param client_factory: Test dependency or input.
    :param status: Test dependency or input.
    :param body: Test dependency or input.
    :param error_name: Test dependency or input.
    :return: Test result or None.
    """
    routes = {("GET", "/api/dates"): {"status": status, "json": body}}
    client, _ = client_factory(routes=routes)
    error_type = getattr(nosible, error_name)

    with pytest.raises(expected_exception=error_type) as raised:
        client.world.dates()

    error = raised.value
    assert isinstance(error, nosible.NosibleAPIError)
    assert isinstance(error, ValueError)
    assert error.status_code == status
    assert error.code == body["error"]
    assert error.method == "GET"
    assert error.path == "/api/dates"
    assert error.body == body


def test_rate_limit_error_exposes_retry_after(
    client_factory: Any
) -> None:
    """

    Verify rate limit error exposes retry after.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    routes = {
        ("GET", "/api/dates"): {
            "status": 429,
            "json": {
                "error": "rate_limited",
                "message": "Quota exhausted.",
            },
            "headers": {"Retry-After": "17"},
        }
    }
    client, _ = client_factory(routes=routes)

    with pytest.raises(expected_exception=nosible.RateLimitError) as raised:
        client.world.dates()

    assert raised.value.retry_after == 17
    assert raised.value.status_code == 429


def test_rate_limit_error_parses_http_date_retry_after(
    client_factory: Any
) -> None:
    """

    Verify rate limit error parses http date retry after.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    retry_at = datetime.now(tz=timezone.utc) + timedelta(seconds=30)
    routes = {
        ("GET", "/api/dates"): {
            "status": 429,
            "json": {
                "error": "rate_limited",
                "message": "Quota exhausted.",
            },
            "headers": {
                "Retry-After": format_datetime(
                    dt=retry_at,
                    usegmt=True
                )
            },
        }
    }
    client, _ = client_factory(routes=routes)

    with pytest.raises(expected_exception=nosible.RateLimitError) as raised:
        client.world.dates()

    assert raised.value.retry_after is not None
    assert 0 <= raised.value.retry_after <= 30


def test_expired_cursor_uses_http_gone_and_specific_error(
    client_factory: Any
) -> None:
    """

    Verify expired cursor uses http gone and specific error.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    routes = {
        ("GET", "/api/entities/events"): {
            "status": 410,
            "json": {
                "error": "cursor_expired",
                "message": "The index was rebuilt; restart pagination.",
            },
        }
    }
    client, _ = client_factory(routes=routes)

    with pytest.raises(expected_exception=nosible.CursorExpiredError) as raised:
        client.world.entity_events(
            entity_type="ORG",
            name="NVIDIA",
            cursor="stale-cursor"
        )

    assert isinstance(raised.value, nosible.NosibleAPIError)
    assert raised.value.status_code == 410
    assert raised.value.code == "cursor_expired"


def test_error_string_contains_actionable_request_context(
    client_factory: Any
) -> None:
    """

    Verify error string contains actionable request context.

    :param client_factory: Test dependency or input.
    :return: Test result or None.
    """
    routes = {
        ("GET", "/api/dates"): {
            "status": 503,
            "json": {
                "error": "backend_unreachable",
                "message": "World backend is unavailable.",
            },
        }
    }
    client, _ = client_factory(routes=routes)

    with pytest.raises(expected_exception=nosible.BackendError) as raised:
        client.world.dates()

    rendered = str(raised.value)
    assert "503" in rendered
    assert "GET" in rendered
    assert "/api/dates" in rendered
    assert "backend_unreachable" in rendered


def test_transient_transport_errors_honor_existing_retry_setting(
    monkeypatch: Any
) -> None:
    """

    Verify transient transport errors honor existing retry setting.

    :param monkeypatch: Test dependency or input.
    :return: Test result or None.
    """
    handler = TransientTransportHandler()
    monkeypatch.setattr(
        target="nosible.transport.time.sleep",
        name=skip_sleep
    )
    http_client = httpx.Client(transport=httpx.MockTransport(handler=handler))
    client = nosible.Nosible(
        nosible_api_key="nos_test_contract",
        http_client=http_client,
        retries=2
    )
    try:
        assert client.world.dates() == {"dates": ["2026-07-20"]}
        assert len(handler.attempts) == 2
    finally:
        client.close()
        http_client.close()


def test_retryable_get_statuses_honor_existing_retry_setting(
    client_factory: Any,
    monkeypatch: Any
) -> None:
    """

    Verify retryable get statuses honor existing retry setting.

    :param client_factory: Test dependency or input.
    :param monkeypatch: Test dependency or input.
    :return: Test result or None.
    """
    client, recorder = client_factory(
        retries=2,
        routes={
            ("GET", "/api/dates"): [
                {
                    "status": 503,
                    "json": {
                        "error": "unavailable",
                        "message": "Temporarily unavailable.",
                    },
                    "headers": {"Retry-After": "0"},
                },
                {"json": {"dates": ["2026-07-20"]}},
            ]
        }
    )
    monkeypatch.setattr(
        target="nosible.transport.time.sleep",
        name=skip_sleep
    )

    assert client.world.dates() == {"dates": ["2026-07-20"]}
    assert len(recorder.requests) == 2


def test_download_disables_injected_http_client_auth() -> None:
    """
    Verify presigned downloads cannot inherit injected client credentials.

    :return: None.
    """
    handler = DownloadTransportHandler(status_codes=[200])
    http_client = httpx.Client(
        transport=httpx.MockTransport(handler=handler),
        auth=ClientBearerAuth()
    )
    client = nosible.Nosible(
        nosible_api_key="nos_test_contract",
        http_client=http_client
    )
    try:
        response = client.transport.download(
            url="https://downloads.example/results.json"
        )
        assert response.status_code == 200
        assert "authorization" not in handler.requests[0].headers
        assert "api-key" not in handler.requests[0].headers
    finally:
        client.close()
        http_client.close()


def test_download_retries_transient_statuses(
    monkeypatch: Any
) -> None:
    """
    Verify presigned downloads retry transient HTTP statuses.

    :param monkeypatch: Active pytest monkeypatch fixture.
    :return: None.
    """
    handler = DownloadTransportHandler(status_codes=[503, 200])
    monkeypatch.setattr(
        target="nosible.transport.time.sleep",
        name=skip_sleep
    )
    http_client = httpx.Client(transport=httpx.MockTransport(handler=handler))
    client = nosible.Nosible(
        nosible_api_key="nos_test_contract",
        http_client=http_client,
        retries=2
    )
    try:
        response = client.transport.download(
            url="https://downloads.example/results.json"
        )
        assert response.status_code == 200
        assert len(handler.requests) == 2
    finally:
        client.close()
        http_client.close()


def skip_sleep(
    seconds: float
) -> None:
    """
    Replace retry sleeping during deterministic contract tests.

    :param seconds: Requested sleep duration.
    :return: None.
    """
