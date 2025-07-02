from __future__ import annotations

from typing import TYPE_CHECKING

from openai import OpenAI

from nosible.classes.web_page import WebPageData

if TYPE_CHECKING:
    from nosible.classes.result_set import ResultSet
else:
    ResultSet = None


class Result:
    """
    Represents a single search result, including metadata and content.

    Attributes
    ----------
    url : str or None
        The URL of the search result.
    title : str or None
        The title of the page or document.
    description : str or None
        A short snippet or description of the result.
    netloc : str or None
        The network location (domain) of the URL.
    published : str or None
        The publication date (ISO formatted date).
    visited : str or None
        When the site was visited (ISO formatted date).
    author : str or None
        The author name or identifier.
    content : str or None
        The full text or HTML content.
    language : str or None
        The language code of the content.
    similarity : float or None
        Similarity score to a query.
    url_hash : str or None
        Hash of the URL for deduplication.

    Methods
    -------
    visit(client)
        Visit the URL associated with this Result and retrieve its content.
    sentiment(client)
        Fetch a sentiment score for this Result via your LLM client.
    similar(client, ...)
        Find similar search results based on the content or metadata of this Result.
    to_dict()
        Convert the Result instance to a dictionary.
    from_dict(data)
        Create a Result instance from a dictionary.

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

    def __init__(
        self,
        url=None,
        title=None,
        description=None,
        netloc=None,
        published=None,
        visited=None,
        author=None,
        content=None,
        language=None,
        similarity=None,
        url_hash=None,
    ):
        """
        Initialize a Result instance with optional metadata fields.

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
        url_hash : str, optional
            A hash value representing the URL for quick comparison or lookup.
        """
        self.url = url
        self.title = title
        self.description = description
        self.netloc = netloc
        self.published = published
        self.visited = visited
        self.author = author
        self.content = content
        self.language = language
        self.similarity = similarity
        self.url_hash = url_hash

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
           N/A | No Title
        """
        similarity = f"{self.similarity:.2f}" if self.similarity is not None else "N/A"
        title = self.title or "No Title"
        return f"{similarity:>6} | {title}"

    def __repr__(self):
        """
        Return a detailed string representation for debugging.

        Returns
        -------
        str
            A string mimicking dataclass auto-generated repr, listing all fields and their values.

        Examples
        --------
        >>> result = Result(url="https://example.com", title="Example Domain")
        >>> print(repr(result))  # doctest: +ELLIPSIS
        Result(url='https://example.com', title='Example Domain', ... url_hash=None)
        """
        # like dataclass’s auto-generated repr
        fields = ", ".join(f"{k}={v!r}" for k, v in self.to_dict().items())
        return f"{self.__class__.__name__}({fields})"

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

    def __getattr__(self, item: str) -> str | float | bool | None:
        """
        Retrieve the value of an attribute by its name using __getitem__.

        Parameters
        ----------
        item : str
            The name of the attribute to retrieve.

        Returns
        -------
        str or float or bool or None
            The value of the requested attribute.

        Raises
        ------
        AttributeError
            If the attribute does not exist in the object.

        Examples
        --------
        >>> result = Result(title="Example Domain", similarity=0.98)
        >>> result.__getattr__("title")
        'Example Domain'
        >>> result.__getattr__("similarity")
        0.98
        >>> result.__getattr__("url") is None
        True
        >>> result.__getattr__("nonexistent")
        Traceback (most recent call last):
            ...
        AttributeError: Attribute 'nonexistent' not found in Result
        """
        try:
            return self.__getitem__(item)
        except KeyError as err:
            raise AttributeError(f"Attribute '{item}' not found in Result") from err

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
        >>> with Nosible() as nos:  # doctest: +SKIP
        ...     result = Result(url="https://example.com")
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
        RuntimeError
            If the API call itself fails.

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
        print(content)
        prompt = f"""
            # TASK DESCRIPTION
            On a scale from -1.0 (very negative) to 1.0 (very positive),
            please rate the sentiment of the following text and return _only_ the numeric score:
            {content.strip()}

            # RESPONSE FORMAT

            The response must be a float in [-1.0, 1.0]. No other text must be returned.
        """

        llm_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=client.llm_api_key)

        # Call the chat completions endpoint.
        resp = llm_client.chat.completions.create(
            model="openai/gpt-4o", messages=[{"role": "user", "content": prompt.strip()}], temperature=0.7
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
        sql_filter: list[str] = None,
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
            SQL filter expressions to apply to the search.
        n_results : int, default 100
            Number of similar results to return.
        n_probes : int, default 30
            Number of probes for the search algorithm.
        n_contextify : int, default 128
            Context window size for the search.
        algorithm : str, default "hybrid-2"
            Search algorithm to use.
        publish_start, publish_end, include_netlocs, exclude_netlocs, visited_start, visited_end, certain,
        include_languages, exclude_languages, include_companies, exclude_companies : optional
            Additional filtering options for the search.

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
        >>> from nosible import Nosible, Result
        >>> with Nosible() as nos:
        ...     result = Result(url="https://example.com", title="Example Domain")
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
            )
            return client.search(s)
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
        # manual replacement for asdict()
        return {
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "netloc": self.netloc,
            "published": self.published,
            "visited": self.visited,
            "author": self.author,
            "content": self.content,
            "language": self.language,
            "similarity": self.similarity,
            "url_hash": self.url_hash,
        }

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
