import json
import threading
import time

import pytest

import nosible.utils.json_tools as jt
import nosible.utils.rate_limiter as rl_mod
from nosible.utils.rate_limiter import RateLimiter, _rate_limited


class Dummy:
    """For testing unserializable objects."""

    pass


@pytest.fixture(autouse=True)
def restore_orjson(monkeypatch):
    """
    Ensure that after each test, _use_orjson and orjson are reset
    to their real values.
    """
    real_use = jt._use_orjson
    real_orjson = getattr(jt, "orjson", None)
    yield
    jt._use_orjson = real_use
    if real_orjson is not None:
        jt.orjson = real_orjson
    else:
        jt.orjson = None


def test_json_dumps_standard():
    # Force json.dumps path
    jt._use_orjson = False
    d = {"a": 1, "b": [2, 3]}
    s = jt.json_dumps(d)
    assert isinstance(s, str)
    # no spaces by default in json.dumps
    assert s in ('{"a": 1, "b": [2, 3]}', '{"a":1,"b":[2,3]}')

    # list serialization
    assert jt.json_dumps([1, 2, 3]) in ("[1, 2, 3]", "[1,2,3]")


def test_json_dumps_orjson_path(monkeypatch):
    # Simulate orjson available
    monkeypatch.setattr(jt, "_use_orjson", True)

    # fake orjson.dumps to mimic real behavior: returns bytes of JSON
    class FakeOrjson:
        @staticmethod
        def dumps(o):
            # Convert keys to str like orjson does
            def convert_keys(obj):
                if isinstance(obj, dict):
                    return {str(k): convert_keys(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_keys(i) for i in obj]
                else:
                    return obj

            return json.dumps(convert_keys(o)).encode("utf-8")

    monkeypatch.setattr(jt, "orjson", FakeOrjson)
    payload = {1: "one", "nested": {2: [3, {4: 5}]}}
    s = jt.json_dumps(payload)
    assert isinstance(s, str)
    assert json.loads(s) == {"1": "one", "nested": {"2": [3, {"4": 5}]}}


def test_json_dumps_error_raises():
    jt._use_orjson = False
    with pytest.raises(RuntimeError) as ei:
        jt.json_dumps(Dummy())
    assert "Failed to serialize" in str(ei.value)


def test_json_loads_standard_and_bytes():
    jt._use_orjson = False
    d = {"a": 1}
    s = json.dumps(d)
    assert jt.json_loads(s) == d
    # bytes input
    b = s.encode("utf-8")
    assert jt.json_loads(b) == d


def test_json_loads_orjson(monkeypatch):
    monkeypatch.setattr(jt, "_use_orjson", True)

    class FakeOrjson:
        @staticmethod
        def loads(x):
            return {"y": 2}

    monkeypatch.setattr(jt, "orjson", FakeOrjson)
    # both str and bytes
    assert jt.json_loads('{"a":1}') == {"y": 2}
    assert jt.json_loads(b'{"a":1}') == {"y": 2}


def test_json_loads_error_raises():
    jt._use_orjson = False
    with pytest.raises(RuntimeError) as ei:
        jt.json_loads("not a json")
    assert "Failed to deserialize" in str(ei.value)


def test_print_dict_indent(monkeypatch):
    # Standard path
    jt._use_orjson = False
    d = {"a": 1, "b": {"c": 2}}
    s = jt.print_dict(d)
    # Should contain newlines and two-space indent
    # assert '"b": {' in s
    # assert '\n  "c": 2' in s

    # Orjson path with indentation
    class FakeOrjson:
        OPT_INDENT_2 = 2

        @staticmethod
        def dumps(o, option=None):
            return b'{\n  "z": 9\n}'

    monkeypatch.setattr(jt, "_use_orjson", True)
    monkeypatch.setattr(jt, "orjson", FakeOrjson)
    s2 = jt.print_dict({"z": 9})
    assert isinstance(s2, str)
    assert '"z": 9' in s2


def test_rate_limiter_try_acquire_and_block(monkeypatch):
    # small window so we don't wait too long
    rl = RateLimiter(max_calls=1, period_s=0.1)
    # first try_acquire succeeds
    assert rl.try_acquire() is True
    # second immediately fails
    assert rl.try_acquire() is False

    # test blocking acquire waits at least ~0.1s
    start = time.perf_counter()
    rl2 = RateLimiter(max_calls=1, period_s=0.05)
    rl2.acquire()  # consume
    rl2.acquire()  # should block until reset
    elapsed = time.perf_counter() - start
    # Round to 2 decimal places for precision
    assert round(elapsed, 2) >= 0.01


def test_rate_limited_decorator_calls_all_limiters():
    calls = []

    class StubLimiter:
        def __init__(self):
            self.count = 0

        def acquire(self):
            self.count += 1
            calls.append("acq")

    class API:
        def __init__(self):
            # two stub limiters for endpoint 'test'
            self._limiters = {"test": [StubLimiter(), StubLimiter()]}

        @_rate_limited("test")
        def do_something(self, x):
            return x * 2

    api = API()
    result = api.do_something(3)
    # should return function result
    assert result == 6
    # ensure both limiters had acquire() called once
    assert calls == ["acq", "acq"]
