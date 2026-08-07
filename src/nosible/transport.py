"""Shared synchronous HTTP transport for NOSIBLE Search and World."""

import os
import time
from typing import Any, Dict, Literal, Optional
from urllib.parse import urlsplit

import httpx

from nosible.exceptions import AuthenticationError, BackendError, error_from_response, parse_retry_after

AUTH_MODE = Literal["search", "world", "none"]
RETRYABLE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


class NosibleTransport:
    """Own URL construction, authentication, retries, and error translation."""

    def __init__(
        self: "NosibleTransport",
        base_url: str,
        api_key: Optional[str],
        client: httpx.Client,
        timeout: float,
        retries: int = 1
    ) -> None:
        """
        Initialize a shared NOSIBLE HTTP transport.

        :param base_url: Absolute merged API base URL.
        :param api_key: NOSIBLE API key when authentication is required.
        :param client: Synchronous HTTPX client.
        :param timeout: Default request timeout in seconds.
        :param retries: Maximum number of transport attempts.
        :return: None.
        """
        base_url = os.fspath(path=base_url)
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("base_url must be a non-empty HTTP(S) URL")
        parsed = urlsplit(
            url=base_url
        )
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("base_url must be an absolute HTTP(S) URL")
        if isinstance(retries, bool) or not isinstance(retries, int) or retries < 1:
            raise ValueError("retries must be a positive integer")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = client
        self.timeout = timeout
        self.retries = retries

    def request_json(
        self: "NosibleTransport",
        method: str,
        path: str,
        auth: AUTH_MODE,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Send a request and parse its JSON response.

        :param method: HTTP request method.
        :param path: API path relative to the merged base URL.
        :param auth: Authentication scheme to apply.
        :param params: Optional query parameters.
        :param json: Optional JSON request body.
        :param timeout: Optional per-request timeout override.
        :return: Parsed JSON response.
        """
        response = self.request(
            method=method,
            path=path,
            auth=auth,
            params=params,
            json=json,
            timeout=timeout
        )
        try:
            return response.json()
        except ValueError as exc:
            raise BackendError(
                message="NOSIBLE returned malformed JSON.",
                status_code=response.status_code,
                code="invalid_json",
                method=response.request.method,
                path=response.request.url.path,
                body=response.text
            ) from exc

    def request(
        self: "NosibleTransport",
        method: str,
        path: str,
        auth: AUTH_MODE,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """
        Send a request with bounded network and safe status retries.

        :param method: HTTP request method.
        :param path: API path relative to the merged base URL.
        :param auth: Authentication scheme to apply.
        :param params: Optional query parameters.
        :param json: Optional JSON request body.
        :param timeout: Optional per-request timeout override.
        :return: Successful HTTP response.
        """
        normalized_method = method.upper()
        credential_headers = self.auth_headers(
            auth=auth
        )
        for attempt in range(self.retries):
            try:
                request = self.client.build_request(
                    method=normalized_method,
                    url=self.url(
                        path=path
                    ),
                    params=params,
                    json=json,
                    headers={"Accept-Encoding": "gzip, zstd"},
                    timeout=self.timeout if timeout is None else timeout
                )
                request.headers.pop("api-key", None)
                request.headers.pop("authorization", None)
                request.headers.update(credential_headers)
                response = self.client.send(
                    request=request,
                    follow_redirects=True,
                    auth=None
                )
            except httpx.RequestError as exc:
                if attempt + 1 == self.retries:
                    raise BackendError(
                        message=str(exc),
                        code="request_error",
                        method=normalized_method,
                        path=urlsplit(
                            url=self.url(
                                path=path
                            )
                        ).path
                    ) from exc
                time.sleep(
                    exponential_delay(
                        attempt=attempt
                    )
                )
                continue
            if should_retry_response(
                response=response,
                method=normalized_method,
                attempt=attempt,
                retries=self.retries
            ):
                time.sleep(
                    response_retry_delay(
                        response=response,
                        attempt=attempt
                    )
                )
                continue
            if response.is_error:
                raise error_from_response(
                    response=response
                )
            return response
        raise BackendError(
            message="NOSIBLE request exhausted all retry attempts.",
            code="retry_exhausted",
            method=normalized_method,
            path=urlsplit(
                url=self.url(
                    path=path
                )
            ).path
        )

    def download(
        self: "NosibleTransport",
        url: str,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """
        Fetch a presigned result without forwarding NOSIBLE credentials.

        :param url: Absolute presigned download URL.
        :param timeout: Optional download timeout override.
        :return: Download HTTP response.
        """
        parsed = urlsplit(
            url=url
        )
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("download_from must be an absolute HTTP(S) URL")
        for attempt in range(self.retries):
            try:
                request = self.client.build_request(
                    method="GET",
                    url=url,
                    headers={"Accept-Encoding": "gzip, zstd"},
                    timeout=self.timeout if timeout is None else timeout
                )
                request.headers.pop("api-key", None)
                request.headers.pop("authorization", None)
                response = self.client.send(
                    request=request,
                    follow_redirects=True,
                    auth=None
                )
                if should_retry_response(
                    response=response,
                    method="GET",
                    attempt=attempt,
                    retries=self.retries
                ):
                    time.sleep(
                        response_retry_delay(
                            response=response,
                            attempt=attempt
                        )
                    )
                    continue
                return response
            except httpx.RequestError as exc:
                if attempt + 1 == self.retries:
                    raise BackendError(
                        message=str(exc),
                        code="download_request_error",
                        method="GET",
                        path=parsed.path
                    ) from exc
                time.sleep(
                    exponential_delay(
                        attempt=attempt
                    )
                )
        raise BackendError(
            message="NOSIBLE download exhausted all retry attempts.",
            code="download_retry_exhausted",
            method="GET",
            path=parsed.path
        )

    def url(
        self: "NosibleTransport",
        path: str
    ) -> str:
        """
        Build an absolute URL from a relative API path.

        :param path: API path relative to the merged base URL.
        :return: Absolute API URL.
        """
        return f"{self.base_url}/{path.lstrip('/')}"

    def auth_headers(
        self: "NosibleTransport",
        auth: AUTH_MODE
    ) -> Dict[str, str]:
        """
        Build endpoint-specific authentication headers.

        :param auth: Authentication scheme to apply.
        :return: Authentication headers for the request.
        """
        if auth == "none":
            return {}
        if not self.api_key:
            raise AuthenticationError(
                message="A NOSIBLE API key is required for programmatic access.",
                code="api_key_required"
            )
        if auth == "search":
            return {"api-key": self.api_key}
        return {"Authorization": f"Bearer {self.api_key}"}


def should_retry_response(
    response: httpx.Response,
    method: str,
    attempt: int,
    retries: int
) -> bool:
    """
    Decide whether a response can be retried without duplicating mutations.

    :param response: HTTP response to evaluate.
    :param method: Normalized HTTP request method.
    :param attempt: Zero-based retry attempt.
    :param retries: Maximum number of attempts.
    :return: True when another safe attempt should be made.
    """
    return (
        method in RETRYABLE_METHODS
        and response.status_code in RETRYABLE_STATUS_CODES
        and attempt + 1 < retries
    )


def response_retry_delay(
    response: httpx.Response,
    attempt: int
) -> float:
    """
    Calculate a response retry delay using Retry-After when available.

    :param response: Retryable HTTP response.
    :param attempt: Zero-based retry attempt.
    :return: Delay in seconds before the next attempt.
    """
    retry_after = parse_retry_after(
        retry_value=response.headers.get("Retry-After")
    )
    if retry_after is not None:
        return retry_after
    return exponential_delay(
        attempt=attempt
    )


def exponential_delay(
    attempt: int
) -> float:
    """
    Calculate the bounded exponential retry delay.

    :param attempt: Zero-based retry attempt.
    :return: Delay in seconds before the next attempt.
    """
    return float(min(2**attempt, 20))
