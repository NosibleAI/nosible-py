import json
from typing import Union

try:
    import orjson

    _use_orjson = True
except ImportError:
    _use_orjson = False

# --------------------------------------------------------------------------------------------------------------
# Utility functions for JSON serialization/deserialization
# --------------------------------------------------------------------------------------------------------------


def json_dumps(obj: object) -> str:
    """
    Returns a JSON byte-string if using orjson, else a unicode str.

    Parameters
    ----------
    obj : object
        Object to serialize; must be JSON-serializable.

    Returns
    -------
    Union[bytes, str]
        If `orjson` is available (`_use_orjson` is True), returns a UTF-8 decoded
        unicode `str`; otherwise, returns a JSON `str` via the standard `json.dumps`.

    Raises
    ------
    RuntimeError
        If serialization fails for any reason.

    Examples
    --------
    # Standard dict serialization (no orjson)
    >>> _use_orjson = False
    >>> json_dumps({"a": 1})
    '{"a":1}'

    # List serialization
    >>> _use_orjson = False
    >>> json_dumps([1, 2, 3])
    '[1,2,3]'

    # orjson path returns unicode str
    >>> import orjson
    >>> _use_orjson = True
    >>> orjson.dumps = lambda o: b'{"b":2}'
    >>> json_dumps({"b": 2})
    '{"b":2}'

    # Non-str dict keys are coerced to str when using orjson
    >>> _use_orjson = True
    >>> orjson.dumps = lambda o: b'{"1":"one"}'
    >>> json_dumps({1: "one"})
    '{"1":"one"}'

    # Error path: un-serializable object
    >>> _use_orjson = False
    >>> class Bad:
    ...     pass
    >>> try:
    ...     json_dumps(Bad())
    ... except RuntimeError as e:
    ...     "Failed to serialize object to JSON" in str(e)
    '{"1":"one"}'
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

    Parameters
    ----------
    s : Union[bytes, str]
        JSON data to deserialize. Can be `bytes` (e.g., from `orjson.dumps`)
        or a unicode `str`.

    Returns
    -------
    dict
        The deserialized Python dictionary.

    Raises
    ------
    RuntimeError
        If deserialization fails (invalid JSON or other error).

    Examples
    --------
    # Standard library path (disable orjson)
    >>> _use_orjson = False
    >>> json_dumps({"a": 1})
    '{"1":"one"}'

    # orjson path with monkey-patched dumping
    >>> _use_orjson = True
    >>> orjson.dumps = lambda o: b'{"b": 2}'
    >>> json_dumps({"b": 2})
    '{"b": 2}'

    # Convert non-str dict keys to str when using orjson
    >>> _use_orjson = True
    >>> orjson.dumps = lambda o: b'{"1": "one"}'
    >>> json_dumps({1: "one"})
    '{"1": "one"}'

    # Error path: object not serializable
    >>> _use_orjson = False
    >>> class Bad:
    ...     pass
    >>> try:
    ...     json_dumps(Bad())
    ... except RuntimeError as e:
    ...     "Failed to serialize" in str(e)
    '{"1": "one"}'
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


def print_dict(dict: dict) -> str:
    """
    Print a dictionary in a readable format.

    Parameters
    ----------
    d : dict
        The dictionary to print.

    Returns
    -------
    None
        This function does not return anything; it prints the dictionary to stdout.
    """
    if _use_orjson:
        return orjson.dumps(dict, option=orjson.OPT_INDENT_2).decode("utf-8")
    return json.dumps(dict, indent=2)
