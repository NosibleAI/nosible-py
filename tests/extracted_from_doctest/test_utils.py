"""Unit tests for JSON and rate-limiter utilities."""

import os
import json
import time

import pytest

from nosible.utils.json_tools import json_dumps, json_loads, print_dict
from nosible.utils.rate_limiter import RateLimiter

TEST_MODULE = os.path.basename(p=__file__)


MODULE_NAME = os.path.basename(p=__file__)


class Unserializable:
    """Value that the standard JSON encoder cannot serialize."""


def test_json_dumps_compact_text() -> None:
    """
    Verify compact JSON serialization.

    :return: None.
    """
    payload = {
        "a": 1,
        "b": [
            2,
            3
        ]
    }
    assert json_dumps(obj=payload) == '{"a":1,"b":[2,3]}'
    assert json_dumps(obj=[1, 2, 3]) == "[1,2,3]"


def test_json_dumps_coerces_integer_keys() -> None:
    """
    Verify JSON serialization follows standard integer-key behavior.

    :return: None.
    """
    payload = {
        1: "one",
        "nested": {
            2: [
                3
            ]
        }
    }
    assert json.loads(s=json_dumps(obj=payload)) == {
        "1": "one",
        "nested": {
            "2": [
                3
            ]
        }
    }


def test_json_dumps_reports_serialization_errors() -> None:
    """
    Verify serialization failures use the stable SDK error.

    :return: None.
    """
    with pytest.raises(
        expected_exception=RuntimeError,
        match="Failed to serialize"
    ):
        json_dumps(obj=Unserializable())


def test_json_loads_accepts_text_and_bytes() -> None:
    """
    Verify JSON deserialization accepts text and bytes.

    :return: None.
    """
    payload = {
        "a": 1
    }
    text = json.dumps(obj=payload)
    assert json_loads(value=text) == payload
    assert json_loads(value=text.encode(encoding="utf-8")) == payload


def test_json_loads_reports_deserialization_errors() -> None:
    """
    Verify malformed JSON uses the stable SDK error.

    :return: None.
    """
    with pytest.raises(
        expected_exception=RuntimeError,
        match="Failed to deserialize"
    ):
        json_loads(value="not json")


def test_print_dict_uses_two_space_indentation() -> None:
    """
    Verify readable dictionary formatting.

    :return: None.
    """
    formatted = print_dict(
        data={
            "a": {
                "b": 1
            }
        }
    )
    assert '\n  "a": {' in formatted
    assert '\n    "b": 1' in formatted


def test_rate_limiter_try_acquire_and_block() -> None:
    """
    Verify non-blocking and blocking rate-limit paths.

    :return: None.
    """
    limiter = RateLimiter(
        max_calls=1,
        period_s=1.0
    )
    assert limiter.try_acquire() is True
    assert limiter.try_acquire() is False

    blocking_limiter = RateLimiter(
        max_calls=1,
        period_s=0.05
    )
    started = time.perf_counter()
    blocking_limiter.acquire()
    blocking_limiter.acquire()
    elapsed = time.perf_counter() - started
    rounded_elapsed = round(
        number=elapsed,
        ndigits=2
    )
    assert rounded_elapsed >= 0.01, MODULE_NAME
