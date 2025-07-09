import json
import os
import pytest

from nosible import Result

def test_result_to_dict_and_str_and_indexing_and_addition():
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
        url_hash="abc123",
    )
    # to_dict
    d = result.to_dict()
    keys = sorted(d.keys())
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

    # __str__
    s = str(Result(title="T", similarity=0.9876))
    assert "0.99" in s and "T" in s
    s = str(Result(title=None, similarity=None))
    assert "N/A" in s and "No Title" in s

    # indexing
    result2 = Result(url=None, title=None, similarity=None)
    assert result2["title"] is None
    assert result2["similarity"] is None
    with pytest.raises(KeyError):
        _ = result2["nope"]

    # adding two Results
    r1 = Result(title="A", similarity=0.1)
    r2 = Result(title="B", similarity=0.2)
    combined = r1 + r2
    from nosible import ResultSet
    assert isinstance(combined, ResultSet)

def test_sentiment_monkeypatch_and_visit():
    # visit via injected client
    class DummyClient:
        llm_api_key = "dummy"
        def visit(self, url):
            return "webpage"

    r = Result(url="u", content="c")
    # monkey-patch sentiment method for coverage
    import types
    def fake_sent(self, client):
        return 0.5
    r.sentiment = types.MethodType(fake_sent, r)
    assert r.sentiment(DummyClient()) == 0.5
