import os
import json
import pytest
from nosible.classes.web_page import WebPageData
from nosible.classes.snippet_set import SnippetSet



def test_visit_data_fixture_is_webpage_data(visit_data):
    assert isinstance(visit_data, WebPageData)
    assert isinstance(visit_data.snippets, SnippetSet)

def test_str_contains_fields_from_visit(visit_data):
    text = str(visit_data)
    for attr in ("languages", "metadata", "page", "request", "snippets"):
        assert f"{attr}=" in text

def test_to_dict_and_write_json_roundtrip(tmp_path, visit_data):
    wpd = visit_data
    d = wpd.to_dict()
    expected_keys = {
        "companies","full_text","languages","metadata",
        "page","request","snippets","statistics","structured","url_tree"
    }
    assert expected_keys.issubset(d.keys())
    assert isinstance(d["snippets"], dict)
    js = wpd.write_json(tmp_path / "test.json")
    assert json.loads(js) == d
    rebuilt = WebPageData.read_json(tmp_path / "test.json")
    assert rebuilt.to_dict() == d
    assert isinstance(rebuilt.snippets, SnippetSet)

def test_save_and_load_roundtrip(tmp_path, visit_data):
    wpd = visit_data
    path = tmp_path / "wpd.json"
    wpd.write_json(str(path))
    assert os.path.exists(path)
    loaded = WebPageData.read_json(path)
    assert loaded.full_text == wpd.full_text
    assert loaded.languages == wpd.languages
    assert loaded.snippets.to_dict() == wpd.snippets.to_dict()
