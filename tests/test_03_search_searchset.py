from nosible import Search, SearchSet
import pytest

s1 = Search(question="Hedge funds seek to expand into private credit", n_results=10)
s2 = Search(question="Nvidia insiders dump more than $1 billion in stock", n_results=10)


def test_search_initialization():
    assert isinstance(s1, Search)
    assert isinstance(s2, Search)
    assert s1.question == "Hedge funds seek to expand into private credit"
    assert s2.question == "Nvidia insiders dump more than $1 billion in stock"


def test_searchset_initialization():
    search_set = SearchSet([s1, s2])

    assert isinstance(search_set, SearchSet)
    assert len(search_set) == 2
    assert search_set[0] == s1
    assert search_set[1] == s2
    assert search_set.searches == [s1, s2]


def test_searchset_iterable():
    search_set = SearchSet([s1, s2])

    assert isinstance(search_set, SearchSet)
    assert all(isinstance(s, Search) for s in search_set)


def test_searchset_access():
    search_set = SearchSet([s1, s2])
    assert search_set[0] == s1
    assert search_set[1] == s2

    with pytest.raises(IndexError):
        _ = search_set[2]  # Accessing out of range index should raise IndexError


# to_dicts
def test_searchset_to_dicts():
    search_set = SearchSet([s1, s2])

    dicts = search_set.to_dicts()
    assert isinstance(dicts, list)
    assert len(dicts) == 2
    assert dicts[0] == s1.to_dict()
    assert dicts[1] == s2.to_dict()


# to_json
def test_searchset_to_json(tmp_path):
    search_set = SearchSet([s1, s2])

    json_str = search_set.to_json()
    assert isinstance(json_str, str)
    assert len(json_str) > 0  # Ensure that the JSON string is not empty

    # save to file and read back
    search_set.to_json(tmp_path / "search_set.json")
    search_set_copy = SearchSet.from_json(tmp_path / "search_set.json")
    assert search_set == search_set_copy


# add a search to the set
def test_searchset_addition():
    search_set = SearchSet([s1])

    search_set.add(s2)
    assert len(search_set) == 2
    assert search_set[1] == s2
