from nosible import Snippet, SnippetSet, WebPageData
import pytest


def test_snippet_initialization(snippets_data):
    # Load page
    assert isinstance(snippets_data, SnippetSet)

    # Iterable
    assert all(isinstance(snippet, Snippet) for snippet in snippets_data)
    # Access by index
    if len(snippets_data) > 0:
        assert isinstance(snippets_data[0], Snippet)
        # assert isinstance(snippets[-1], Snippet)
    # Access by key
    if len(snippets_data) > 0:
        assert isinstance(snippets_data[0].content, str)


def test_snippet_set_to_dict(snippets_data):
    dicts = snippets_data.to_dict()
    assert isinstance(dicts, dict)
    assert all(isinstance(d, dict) for d in dicts.values())
    assert all("content" in d for d in dicts.values())
