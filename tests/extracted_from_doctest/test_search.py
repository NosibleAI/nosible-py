import pytest
from nosible.classes.search import Search

def test_search_initialization():
    s = Search(
        question="What is Python?",
        n_results=5,
        include_languages=["en"],
        publish_start="2023-01-01",
        publish_end="2023-12-31",
        certain=True,
    )
    assert s.question == "What is Python?"
    assert s.n_results == 5
    assert s.include_languages == ["en"]
    assert s.publish_start == "2023-01-01"
    assert s.publish_end == "2023-12-31"
    assert s.certain is True

def test_search_to_dict_and_from_dict():
    params = {
        "question": "What is Python?",
        "n_results": 10,
        "include_languages": ["en"],
        "publish_start": "2023-01-01",
        "certain": True,
    }
    s = Search.from_dict(params)
    d = s.to_dict()
    assert d["question"] == "What is Python?"
    s2 = Search.from_dict(d)
    assert s2.question == s.question
    assert s2.n_results == s.n_results

def test_search_save_and_load(tmp_path):
    s = Search(question="What is Python?", n_results=3, include_languages=["en"], publish_start="2023-01-01")
    file_path = tmp_path / "search.json"
    s.write_json(file_path)
    assert file_path.exists()
    loaded = Search.read_json(file_path)
    assert isinstance(loaded, Search)
    assert loaded.question == s.question

def test_search_addition_combines_into_searchset():
    from nosible.classes.search_set import SearchSet
    s1 = Search(question="Q1")
    s2 = Search(question="Q2")
    combined = s1 + s2
    assert isinstance(combined, SearchSet)
    assert len(combined.searches) == 2
