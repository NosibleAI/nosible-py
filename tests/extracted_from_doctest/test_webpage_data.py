"""Tests for test webpage data."""

import os
import json
from typing import Any

from nosible.classes.snippet_set import SnippetSet
from nosible.classes.web_page import WebPageData

TEST_MODULE = os.path.basename(p=__file__)


def test_scrape_url_data_fixture_is_webpage_data(
    scrape_url_data: Any
) -> None:
    """

    Verify scrape url data fixture is webpage data.

    :param scrape_url_data: Test dependency or input.
    :return: Test result or None.
    """
    assert isinstance(scrape_url_data, WebPageData)
    assert isinstance(scrape_url_data.snippets, SnippetSet)


def test_str_contains_fields_from_scrape(
    scrape_url_data: Any
) -> None:
    """

    Verify str contains fields from scrape.

    :param scrape_url_data: Test dependency or input.
    :return: Test result or None.
    """
    text = str(scrape_url_data)
    for attr in ("languages", "metadata", "page", "request", "snippets"):
        assert f"{attr}=" in text


def test_to_dict_and_write_json_roundtrip(
    tmp_path: Any,
    scrape_url_data: Any
) -> None:
    """

    Verify to dict and write json roundtrip.

    :param tmp_path: Test dependency or input.
    :param scrape_url_data: Test dependency or input.
    :return: Test result or None.
    """
    web_page = scrape_url_data
    payload = web_page.to_dict()
    expected_keys = {
        "full_text","languages","metadata",
        "page","request","snippets","statistics","structured","url_tree"
    }
    assert expected_keys.issubset(payload.keys())
    assert isinstance(payload["snippets"], dict)
    json_text = web_page.write_json(path=tmp_path / "test.json")
    assert json.loads(s=json_text) == payload
    rebuilt = WebPageData.read_json(path=tmp_path / "test.json")
    assert rebuilt.to_dict() == payload
    assert isinstance(rebuilt.snippets, SnippetSet)


def test_save_and_load_roundtrip(
    tmp_path: Any,
    scrape_url_data: Any
) -> None:
    """

    Verify save and load roundtrip.

    :param tmp_path: Test dependency or input.
    :param scrape_url_data: Test dependency or input.
    :return: Test result or None.
    """
    web_page = scrape_url_data
    path = tmp_path / "wpd.json"
    web_page.write_json(path=str(path))
    assert os.path.exists(path)
    loaded = WebPageData.read_json(path=path)
    assert loaded.full_text == web_page.full_text
    assert loaded.languages == web_page.languages
    assert loaded.snippets.to_dict() == web_page.snippets.to_dict()
