from typing import Union

try:
    import orjson

    _use_orjson = True
except ImportError:
    import json

    _use_orjson = False

# --------------------------------------------------------------------------------------------------------------
# Utility functions for JSON serialization/deserialization
# --------------------------------------------------------------------------------------------------------------


def json_dumps(obj: object) -> Union[bytes, str]:
    """
    Returns a JSON byte-string if using orjson, else a unicode str.
    """
    try:
        if _use_orjson:
            # Ensure all dict keys are str for orjson
            def ensure_str_keys(o):
                if isinstance(o, dict):
                    return {str(k): ensure_str_keys(v) for k, v in o.items()}
                if isinstance(o, list):
                    return [ensure_str_keys(i) for i in o]
                return o

            obj = ensure_str_keys(obj)
            return orjson.dumps(obj).decode("utf-8")  # decode to str for consistency
        return json.dumps(obj)
    except Exception as e:
        # Optionally, you can log the error here
        raise RuntimeError(f"Failed to serialize object to JSON: {e}") from e


def json_loads(s: Union[bytes, str]) -> dict:
    """
    Accept both bytes (from orjson) and str (from json.loads).
    """
    try:
        if _use_orjson:
            # orjson.loads accepts both bytes and str today
            return orjson.loads(s)
        # If we accidentally passed bytes, decode to str first
        if isinstance(s, (bytes, bytearray)):
            s = s.decode("utf-8")
        return json.loads(s)
    except Exception as e:
        # Optionally, you can log the error here
        raise RuntimeError(f"Failed to deserialize JSON: {e}") from e
