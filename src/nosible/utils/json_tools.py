"""JSON serialization helpers used across the NOSIBLE client."""

import os
import json
from typing import Any, Dict, Union

MODULE_NAME = os.path.basename(p=__file__)


def json_dumps(
    obj: object
) -> str:
    """
    Serialize an object to compact JSON.

    :param obj: JSON-serializable object.
    :return: Compact JSON string.
    """
    try:
        return json.dumps(
            obj=obj,
            separators=(",", ":")
        )
    except (TypeError, ValueError, OverflowError) as error:
        raise RuntimeError(
            f"{MODULE_NAME}: Failed to serialize object to JSON: {error}"
        ) from error


def json_loads(
    value: Union[bytes, bytearray, str]
) -> Any:
    """
    Deserialize JSON supplied as bytes or text.

    :param value: JSON bytes or text.
    :return: Deserialized JSON value.
    """
    if isinstance(value, (bytes, bytearray)):
        value = value.decode(encoding="utf-8")
    try:
        return json.loads(s=value)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"{MODULE_NAME}: Failed to deserialize JSON: {error}"
        ) from error


def print_dict(
    data: Dict[str, Any]
) -> str:
    """
    Format a dictionary as indented JSON.

    :param data: Dictionary to format.
    :return: Indented JSON string.
    """
    try:
        return json.dumps(
            obj=data,
            indent=2
        )
    except (TypeError, ValueError, OverflowError) as error:
        raise RuntimeError(
            f"{MODULE_NAME}: Failed to format dictionary: {error}"
        ) from error


def ensure_str_keys(
    value: Any
) -> Any:
    """
    Recursively coerce dictionary keys to strings.

    :param value: Value whose nested dictionary keys should be normalized.
    :return: Value with string dictionary keys.
    """
    if isinstance(value, dict):
        return {
            str(key): ensure_str_keys(value=item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            ensure_str_keys(value=item)
            for item in value
        ]
    return value
