import pytest
from nosible.classes.search import Search
from nosible.classes.search_set import SearchSet

def test_searchset_basic_operations(tmp_path):
    s1 = Search(question="What is Python?", n_results=3)
    s2 = Search(question="What is PEP8?", n_results=2)
    ss = SearchSet([s1, s2])

    # __str__
    lines = str(ss).splitlines()
    assert lines[0].startswith("0: What is Python?")
    assert lines[1].startswith("1: What is PEP8?")

    # add/remove/len
    s3 = Search(question="What is AI?", n_results=1)
    ss.add(s3)
    assert len(ss) == 3 and ss[2].question == "What is AI?"
    ss.remove(1)
    assert [s.question for s in ss.searches_list] == ["What is Python?", "What is AI?"]

    # to_dicts/write_json round-trip
    dicts = ss.to_dicts()
    assert isinstance(dicts, list) and dicts[0]["question"] == "What is Python?"
    js = ss.write_json()
    assert isinstance(js, str)
    ss.write_json(tmp_path / "searches.json")
    loaded = SearchSet.read_json(tmp_path / "searches.json")
    assert [s.question for s in loaded.searches_list] == [s.question for s in ss.searches_list]
