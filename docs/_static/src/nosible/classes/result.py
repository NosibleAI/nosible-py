from __future__ import annotations

from typing import TYPE_CHECKING

from openai import OpenAI

from nosible.classes.web_page import WebPageData

if TYPE_CHECKING:
    from nosible.classes.result_set import ResultSet


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
        >>> from nosible import Nosible  # doctest: +SKIP
        >>> with Nosible() as nos:  # doctest: +SKIP
        ...     results = nos.search(question="Nvidia market performance", n_results=10)  # doctest: +SKIP
        ...     for result in results:  # doctest: +SKIP
        ...         sentiment = result.sentiment(client=nos)  # doctest: +SKIP
        ...         print(sentiment)  # doctest: +SKIP
        TODO Add example
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
