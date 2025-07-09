import pytest
import json
from nosible.classes.snippet_set import SnippetSet



def test_snippetset_len_getitem_index_error(snippets_data):
    ss = snippets_data
    assert len(ss) == ss.__len__()
    if len(ss) > 0:
        assert isinstance(ss[0], type(ss[0]))
    with pytest.raises(IndexError):
        _ = ss[len(ss)]

def test_snippetset_iteration_and_str_reset(snippets_data):
    ss = snippets_data
    contents = [s.content for s in ss]
    assert contents == [s.content for s in ss]
    itr = iter(ss)
    result = []
    with pytest.raises(StopIteration):
        for _ in range(len(ss) + 1):
            result.append(next(itr))
    assert len(result) == len(contents)

def test_snippetset_to_dict_and_json_roundtrip(snippets_data):
    ss = snippets_data
    d = ss.to_dict()
    assert isinstance(d, dict)
    for inner in d.values():
        assert isinstance(inner, dict) and "content" in inner
    js = ss.to_json()
    assert json.loads(js) == d
    rebuilt = SnippetSet.from_dict(d)
    assert [s.content for s in rebuilt] == [s.content for s in ss]
