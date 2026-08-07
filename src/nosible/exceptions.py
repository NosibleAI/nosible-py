"""Stable exception types raised by the NOSIBLE clients."""

import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Optional, Tuple, Type

import httpx


class NosibleAPIError(ValueError):
    """Base class for errors returned by a NOSIBLE HTTP endpoint."""

    def __init__(
        self: "NosibleAPIError",
        message: str,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
        body: Any = None,
        retry_after: Optional[float] = None
    ) -> None:
        """
        Initialize an API error with stable request context.

        :param message: Human-readable error message.
        :param status_code: HTTP status code when a response was received.
        :param code: Stable NOSIBLE error code.
        :param method: HTTP request method.
        :param path: HTTP request path.
        :param body: Parsed or raw response body.
        :param retry_after: Suggested retry delay in seconds.
        :return: None.
        """
        self.status_code = status_code
        self.code = code
        self.method = method
        self.path = path
        self.body = body
        self.retry_after = retry_after
        super().__init__(message)

    def __str__(
        self: "NosibleAPIError"
    ) -> str:
        """
        Render the error with actionable request context.

        :return: Human-readable error string.
        """
        context = " ".join(
            str(value)
            for value in (self.status_code, self.method, self.path, self.code)
            if value is not None
        )
        message = super().__str__()
        return f"{context}: {message}" if context else message


class AuthenticationError(NosibleAPIError):
    """The request did not carry valid API credentials."""


class ValidationError(NosibleAPIError):
    """The request failed local or remote validation."""


class RateLimitError(NosibleAPIError):
    """A NOSIBLE rate limit was exhausted."""


class ConflictError(NosibleAPIError):
    """The requested operation conflicts with current server state."""


class GoneError(NosibleAPIError):
    """The requested resource is no longer available."""


class CursorExpiredError(GoneError):
    """A pagination cursor refers to an index generation that has expired."""


class AccessDeniedError(NosibleAPIError):
    """The credential is valid but cannot access the requested resource."""


class NotFoundError(NosibleAPIError):
    """The requested resource was not found."""


class BackendError(NosibleAPIError):
    """NOSIBLE or an upstream service could not complete the request."""


def error_from_response(
    response: httpx.Response
) -> NosibleAPIError:
    """
    Create the stable SDK exception corresponding to an HTTP response.

    :param response: HTTP response containing a NOSIBLE error.
    :return: Typed API error carrying response context.
    """
    body = response_body(
        response=response
    )
    status = response.status_code
    code, message = error_details(
        body=body,
        status_code=status
    )
    error_type = error_type_for_status(
        status_code=status,
        code=code
    )
    retry_after = parse_retry_after(
        retry_value=response.headers.get("Retry-After")
    )
    return error_type(
        message=message,
        status_code=status,
        code=code,
        method=response.request.method,
        path=response.request.url.path,
        body=body,
        retry_after=retry_after
    )


def response_body(
    response: httpx.Response
) -> Any:
    """
    Parse an HTTP response body without hiding malformed JSON.

    :param response: HTTP response to parse.
    :return: Parsed JSON body or raw response text.
    """
    try:
        return response.json()
    except (TypeError, ValueError):
        return response.text


def error_details(
    body: Any,
    status_code: int
) -> Tuple[str, str]:
    """
    Extract a stable code and message from an error body.

    :param body: Parsed or raw response body.
    :param status_code: HTTP status code.
    :return: Tuple containing the error code and message.
    """
    if isinstance(body, dict):
        code = str(
            body.get("error")
            or body.get("code")
            or f"http_{status_code}"
        )
        message = body.get("message")
        if message is None:
            message = body.get("detail")
        if isinstance(message, (dict, list)):
            message = str(message)
        return code, str(message or code)
    return f"http_{status_code}", str(body or f"HTTP {status_code}")


def error_type_for_status(
    status_code: int,
    code: str
) -> Type[NosibleAPIError]:
    """
    Select the public exception type for an HTTP status.

    :param status_code: HTTP status code.
    :param code: Stable NOSIBLE error code.
    :return: Exception class corresponding to the response.
    """
    if status_code == 401:
        return AuthenticationError
    if status_code == 403:
        return AccessDeniedError
    if status_code in {400, 422}:
        return ValidationError
    if status_code == 404:
        return NotFoundError
    if status_code == 409:
        return ConflictError
    if status_code == 410:
        return CursorExpiredError if code == "cursor_expired" else GoneError
    if status_code == 429:
        return RateLimitError
    if status_code >= 500:
        return BackendError
    return NosibleAPIError


def parse_retry_after(
    retry_value: Optional[str]
) -> Optional[float]:
    """
    Parse numeric and HTTP-date Retry-After header values.

    :param retry_value: Raw Retry-After header value.
    :return: Non-negative retry delay in seconds when parseable.
    """
    if not retry_value:
        return None
    retry_value = os.fspath(path=retry_value)
    try:
        return max(float(retry_value), 0.0)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(
                data=retry_value
            )
        except (TypeError, ValueError):
            return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(
            tzinfo=timezone.utc
        )
    now = datetime.now(
        tz=timezone.utc
    )
    return max((retry_at - now).total_seconds(), 0.0)
