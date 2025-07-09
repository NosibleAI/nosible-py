import pytest
import json
from nosible.classes.snippet import Snippet
from nosible.classes.snippet_set import SnippetSet



def test_snippet_initialization_and_attrs(snippets_data):
    assert isinstance(snippets_data, SnippetSet)
    for snippet in snippets_data:
        assert isinstance(snippet, Snippet)
        assert isinstance(snippet.content, str)

def test_snippet_getitem_and_str(snippets_data):
    ss = snippets_data
    if len(ss) == 0:
        pytest.skip("no snippets to test getitem/str")
    snippet = ss[0]
    assert snippet["content"] == snippet.content
    with pytest.raises(KeyError):
        _ = snippet["nonexistent_field"]

def test_snippet_to_dict_and_json(snippets_data):
    ss = snippets_data
    if len(ss) == 0:
        pytest.skip("no snippets to test to_dict/to_json")
    snippet = ss[0]
    d = snippet.to_dict()
    assert isinstance(d, dict) and "content" in d
    js = snippet.to_json()
    assert json.loads(js) == d
