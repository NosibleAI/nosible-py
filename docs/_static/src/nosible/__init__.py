"""
Nosible package initialization.

This package provides the main interface and core components for interacting with the Nosible client.

Attributes
----------
Nosible : nosible.nosible_client.Nosible
    The main client for interacting with Nosible services.
Search : nosible.classes.search.Search
    Class for constructing search queries.
SearchSet : nosible.classes.search_set.SearchSet
    Class for managing collections of searches.
Result : nosible.classes.result.Result
    Class for handling individual search results.
ResultSet : nosible.classes.result_set.ResultSet
    Class for processing sets of search results.
Snippet : nosible.classes.snippet.Snippet
    Class representing a snippet of information.
SnippetSet : nosible.classes.snippet_set.SnippetSet
    Class for managing collections of snippets.
WebPageData : nosible.classes.web_page.WebPageData
    Class representing web page data.

"""
from nosible.classes.result import Result
from nosible.classes.result_set import ResultSet
from nosible.classes.search import Search
from nosible.classes.search_set import SearchSet
from nosible.classes.snippet import Snippet
from nosible.classes.snippet_set import SnippetSet
from nosible.classes.web_page import WebPageData
from nosible.nosible_client import Nosible

__all__ = [
    "Nosible",
    "Result",
    "ResultSet",
    "Search",
    "SearchSet",
    "Snippet",
    "SnippetSet",
    "WebPageData",
]
