from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from nosible.classes.web_page import WebPageData
from nosible.utils.json_tools import print_dict

if TYPE_CHECKING:
    from nosible.classes.result_set import ResultSet
else:
    ResultSet = None


@dataclass(init=True, repr=True, eq=True, frozen=False)
class Result:
    """
    Represents a single search result, including metadata and content.

    Parameters
    ----------
    url : str, optional
        The URL of the search result.
    title : str, optional
        The title of the search result.
    description : str, optional
        A brief description or summary of the search result.
    netloc : str, optional
        The network location (domain) of the URL.
    published : datetime or str, optional
        The publication date of the search result.
    visited : datetime or str, optional
        The date and time when the result was visited.
    author : str, optional
        The author of the content.
    content : str, optional
        The main content or body of the search result.
    language : str, optional
        The language code of the content (e.g., 'en' for English).
    similarity : float, optional
        Similarity score with respect to a query or reference.

    Examples
    --------
    >>> result = Result(
    ...     url="https://example.com",
    ...     title="Example Domain",
    ...     description="This domain is for use in illustrative examples.",
    ...     netloc="example.com",
    ...     published="2024-01-01",
    ...     visited="2024-01-01",
    ...     author="Example Author",
    ...     content="<html>...</html>",
    ...     language="en",
    ...     similarity=0.98,
    ...     url_hash="abc123",
    ... )
    >>> print(result.title)
    Example Domain
    >>> result_dict = result.to_dict()
    >>> sorted(result_dict.keys())  # doctest: +ELLIPSIS
    ['author', 'content', 'description', 'language', 'netloc', 'published', ... 'visited']
    """

    url: str | None = None
    """The URL of the search result."""
    title: str | None = None
    """The title of the search result."""
    description: str | None = None
    """A brief description or summary of the search result."""
    netloc: str | None = None
    """The network location (domain) of the URL."""
    published: str | None = None
    """The publication date of the search result."""
    visited: str | None = None
    """The date and time when the result was visited."""
    author: str | None = None
    """The author of the content."""
    content: str | None = None
    """The main content or body of the search result."""
    language: str | None = None
    """The language code of the content (e.g., 'en' for English)."""
    similarity: float | None = None
    """Similarity score with respect to a query or reference."""
    url_hash: str | None = None
    """A hash of the URL for quick comparisons."""

    def __str__(self) -> str:
        """
        Return a short summary of the Result.

        Returns
        -------
        str
            A formatted string showing the title, similarity, and URL of the Result.

        Examples
        --------
        >>> result = Result(title="Example Domain", similarity=0.9876)
        >>> print(str(result))
          0.99 | Example Domain
        >>> result = Result(title=None, similarity=None)
        >>> print(str(result))
        {
            "url": null,
            "title": null,
            "description": null,
            "netloc": null,
            "published": null,
            "visited": null,
            "author": null,
            "content": null,
            "language": null,
            "similarity": null,
            "url_hash": null
        }
        """
        return print_dict(self.to_dict())

    def __getitem__(self, key: str) -> str | float | bool | None:
        """
        Retrieve the value of a field by its key.

        Parameters
        ----------
        key : str
            The name of the field to retrieve.

        Returns
        -------
        str or float or bool or None
            The value associated with the specified key.

        Raises
        ------
        KeyError
            If the key does not exist in the object.

        Examples
        --------
        >>> result = Result(title="Example Domain", similarity=0.98)
        >>> result["title"]
        'Example Domain'
        >>> result["similarity"]
        0.98
        >>> result["url"] is None
        True
        >>> result["nonexistent"]
        Traceback (most recent call last):
            ...
        KeyError: "Key 'nonexistent' not found in Result"
        """
        try:
            return object.__getattribute__(self, key)
        except AttributeError as err:
            raise KeyError(f"Key '{key}' not found in Result") from err

    def __add__(self, other: Result) -> ResultSet:
        """
        Combine two Result instances into a ResultSet.

        This method allows you to add two Result objects together, returning a ResultSet
        containing both results.

        Parameters
        ----------
        other : Result
            Another Result instance to combine with this one.

        Returns
        -------
        ResultSet
            A ResultSet containing both this and the other Result.

        Examples
        --------
        >>> from nosible import Result, ResultSet
        >>> r1 = Result(title="First Result", similarity=0.9)
        >>> r2 = Result(title="Second Result", similarity=0.8)
        >>> combined = r1 + r2
        >>> isinstance(combined, ResultSet)
        True
        """
        from nosible.classes.result_set import ResultSet

        return ResultSet([self, other])

    def visit(self, client) -> WebPageData:
        """
        Visit the URL associated with this Result and retrieve its content.

        This method uses the provided Nosible client to fetch the web page content for the given URL.
        The result is returned as a WebPageData object containing the page's content and metadata.

        Parameters
        ----------
        client : Nosible
            An instance of the Nosible client to use for fetching the web page.

        Returns
        -------
        WebPageData
            An object containing the fetched web page's content and metadata.

        Raises
        ------
        ValueError
            If the Result does not have a URL.
        RuntimeError
            If fetching the web page fails.

        Examples
        --------
        >>> from nosible import Nosible, Result
        >>> with Nosible() as nos:
        ...     result = Result(url="https://www.dailynewsegypt.com/2023/09/08/g20-and-its-summits/")
        ...     page = result.visit(client=nos)
        ...     isinstance(page, WebPageData)
        True
        """
        if not self.url:
            raise ValueError("Cannot visit Result without a URL.")
        try:
            return client.visit(url=self.url)
        except Exception as e:
            raise RuntimeError(f"Failed to visit URL '{self.url}': {e}") from e

    def sentiment(self, client) -> float:
        """
        Fetch a sentiment score for this Result via your LLM client, ensuring
        the result is a float in [-1.0, 1.0].

        Parameters
        ----------
        client : Nosible
            An instance of your Nosible client with `.llm_api_key` on it.

        Returns
        -------
        float
            Sentiment score in [-1.0, 1.0].

        Raises
        ------
        ValueError
            If `client` or `client.llm_api_key` is missing, if the LLM response
            is not parseable as a float, or if it falls outside [-1.0, 1.0].

        Examples
        --------
        >>> from nosible.classes.result import Result
        >>> class DummyClient:
        ...     llm_api_key = "dummy"
        ...
        ...     def visit(self, url):
        ...         return "web page"
        >>> result = Result(url="https://example.com", content="This is great!")
        >>> import types
        >>> def fake_sentiment(self, client):
        ...     return 0.8
        >>> result.sentiment = types.MethodType(fake_sentiment, result)
        >>> result.sentiment(DummyClient())
        0.8

        >>> result = Result(url="https://example.com", content="Awful experience.")
        >>> def fake_sentiment_neg(self, client):
        ...     return -0.9
        >>> result.sentiment = types.MethodType(fake_sentiment_neg, result)
        >>> result.sentiment(DummyClient())
        -0.9

        >>> class NoKeyClient:
        ...     llm_api_key = None
        >>> result = Result(url="https://example.com", content="Neutral.")
        >>> try:
        ...     result.sentiment(NoKeyClient())
        ... except ValueError as e:
        ...     print("ValueError" in str(e))
        False

        >>> class NoneClient:
        ...     pass
        >>> result = Result(url="https://example.com", content="Neutral.")
        >>> try:
        ...     result.sentiment(None)
        ... except ValueError as e:
        ...     print("A Nosible client instance must be provided" in str(e))
        True
        """
        if client is None:
            raise ValueError("A Nosible client instance must be provided as 'client'.")
        if not client.llm_api_key:
            raise ValueError("LLM API key is required for getting result sentiment.")

        content = self.content

        prompt = f"""
            # TASK DESCRIPTION
            On a scale from -1.0 (very negative) to 1.0 (very positive),
            please rate the sentiment of the following text and return _only_ the numeric score:
            {content.strip()}

            # RESPONSE FORMAT

            The response must be a float in [-1.0, 1.0]. No other text must be returned.
        """
        from openai import OpenAI
        llm_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=client.llm_api_key)

        # Call the chat completions endpoint.
        resp = llm_client.chat.completions.create(
            model=client.sentiment_model, messages=[{"role": "user", "content": prompt.strip()}], temperature=0.7
        )

        raw = resp.choices[0].message.content

        # Parse and validate
        try:
            score = float(raw)
        except ValueError:
            raise ValueError(f"Sentiment response is not a float: {raw!r}")

        if not -1.0 <= score <= 1.0:
            raise ValueError(f"Sentiment {score} outside valid range [-1.0, 1.0]")

        return score

    def similar(
        self,
        client,
        sql_filter: str = None,
        n_results: int = 100,
        n_probes: int = 30,
        n_contextify: int = 128,
        algorithm: str = "hybrid-2",
        publish_start: str = None,
        publish_end: str = None,
        include_netlocs: list = None,
        exclude_netlocs: list = None,
        visited_start: str = None,
        visited_end: str = None,
        certain: bool = None,
        include_languages: list = None,
        exclude_languages: list = None,
        include_companies: list = None,
        exclude_companies: list = None,
        include_docs: list = None,
        exclude_docs: list = None,
    ) -> ResultSet:
        """
        Find similar search results based on the content or metadata of this Result.

        This method uses the provided Nosible client to find other results
        that are similar to this one, based on its title and optional filters.

        Parameters
        ----------
        client : Nosible
            An instance of the Nosible client to use for finding similar results.
        sql_filter : list of str, optional
            SQL‐style filter clauses.
        n_results : int
            Max number of results (max 100).
        n_probes : int
            Number of index shards to probe.
        n_contextify : int
            Context window size per result.
        algorithm : str
            Search algorithm type.
        publish_start : str, optional
            Start date for when the document was published (ISO format).
        publish_end : str, optional
            End date for when the document was published (ISO format).
        visited_start : str, optional
            Start date for when the document was visited by NOSIBLE (ISO format).
        visited_end : str, optional
            End date for when the document was visited by NOSIBLE (ISO format).
        certain : bool, optional
            Only include documents where we are 100% sure of the date.
        include_netlocs : list of str, optional
            List of netlocs (domains) to include in the search. (Max: 50)
        exclude_netlocs : list of str, optional
            List of netlocs (domains) to exclude in the search. (Max: 50)
        include_languages : list of str, optional
            Languages to include in the search. (Max: 50, ISO 639-1 language codes).
        exclude_languages : list of str, optional
            Language codes to exclude in the search (Max: 50, ISO 639-1 language codes).
        include_companies : list of str, optional
            Google KG IDs of public companies to require (Max: 50).
        exclude_companies : list of str, optional
            Google KG IDs of public companies to forbid (Max: 50).
        include_docs : list of str, optional
            URL hashes of docs to include (Max: 50).
        exclude_docs : list of str, optional
            URL hashes of docs to exclude (Max: 50).

        Returns
        -------
        ResultSet
            A ResultSet object containing similar results.

        Raises
        ------
        ValueError
            If the Result does not have a URL or client is not provided.
        RuntimeError
            If finding similar results fails.

        Examples
        --------
        >>> from nosible import Nosible, Result  # doctest: +SKIP
        >>> with Nosible() as nos:  # doctest: +SKIP
        ...     result = Result(url="https://example.com", title="Example Domain")  # doctest: +SKIP
        ...     similar_results = result.similar(client=nos)  # doctest: +SKIP
        """
        if client is None:
            raise ValueError("A Nosible client instance must be provided as 'client'.")
        if not self.url:
            raise ValueError("Cannot find similar results without a URL.")
        try:
            from nosible import Search

            exclude_companies = [self.url_hash] if not exclude_companies else exclude_companies.append(self.url_hash)
            s = Search(
                question=self.title,
                expansions=[],
                n_results=n_results,
                sql_filter=sql_filter,
                n_probes=n_probes,
                n_contextify=n_contextify,
                algorithm=algorithm,
                publish_start=publish_start,
                publish_end=publish_end,
                include_netlocs=include_netlocs,
                exclude_netlocs=exclude_netlocs,
                visited_start=visited_start,
                visited_end=visited_end,
                certain=certain,
                include_languages=include_languages,
                exclude_languages=exclude_languages,
                include_companies=include_companies,
                exclude_companies=exclude_companies,
                include_docs=include_docs,
                exclude_docs=exclude_docs,
            )
            return client.search(search=s)
        except Exception as e:
            raise RuntimeError(f"Failed to find similar results for title '{self.title}': {e}") from e

    def to_dict(self):
        """
        Convert the Result instance to a dictionary.

        Returns
        -------
        dict
            A dictionary containing all fields of the Result.

        Examples
        --------
        >>> result = Result(
        ...     url="https://example.com",
        ...     title="Example Domain",
        ...     description="A domain used for illustrative examples.",
        ...     netloc="example.com",
        ...     published="2024-01-01",
        ...     visited="2024-01-01",
        ...     author="Example Author",
        ...     content="<html>...</html>",
        ...     language="en",
        ...     similarity=0.95,
        ...     url_hash="abc123",
        ... )
        >>> d = result.to_dict()
        >>> d["title"]
        'Example Domain'
        >>> d["visited"]
        '2024-01-01'
        """
        return asdict(self, dict_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> Result:
        """
        Create a Result instance from a dictionary.

        Parameters
        ----------
        data : dict
            Dictionary containing the fields of the Result.

        Returns
        -------
        Result
            An instance of Result populated with the provided data.

        Examples
        --------
        >>> data = {
        ...     "url": "https://example.com",
        ...     "title": "Example Domain",
        ...     "description": "A domain used for illustrative examples.",
        ...     "netloc": "example.com",
        ...     "published": "2024-01-01",
        ...     "visited": "2024-01-01",
        ...     "author": "Example Author",
        ...     "content": "<html>...</html>",
        ...     "language": "en",
        ...     "similarity": 0.95,
        ...     "url_hash": "abc123",
        ... }
        >>> result = Result.from_dict(data)
        >>> result.title
        'Example Domain'
        """
        return cls(**data)
