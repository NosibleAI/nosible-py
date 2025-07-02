import gzip
import json
import logging
import os
import time
import traceback
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union

import polars as pl
import requests
from cryptography.fernet import Fernet
from openai import OpenAI
from polars import SQLContext
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
)

from nosible.classes.result_set import ResultSet
from nosible.classes.search import Search
from nosible.classes.search_set import SearchSet
from nosible.classes.web_page import WebPageData
from nosible.utils.json_tools import json_loads
from nosible.utils.rate_limiter import PLAN_RATE_LIMITS, RateLimiter, _rate_limited

# Set up a module‐level logger.
logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

logging.disable(logging.CRITICAL)


class Nosible:
    """
    High-level client for the Nosible Search API.

    Attributes
    ----------
    nosible_api_key : str
        API key for the Nosible Search API.
    llm_api_key : str
        API key for LLM-based query expansions.
    openai_base_url : str
        Base URL for the OpenAI-compatible LLM API.
    sentiment_model : str
        Model to use for sentiment analysis and expansions.
    timeout : int
        Request timeout for HTTP calls.
    retries : int
        Number of retry attempts for transient HTTP errors.
    concurrency : int
        Maximum concurrent search requests.
    headers : dict
        Default HTTP headers for API requests.
    logger : logging.Logger
        Logger instance for this client.
    _session : requests.Session
        HTTP session for persistent connections.
    _executor : ThreadPoolExecutor
        Thread pool for concurrent searches.
    _limiters : dict
        Rate limiter objects for each endpoint.
    publish_start, publish_end, include_netlocs, exclude_netlocs, visited_start, visited_end, certain,
    include_languages, exclude_languages, include_companies, exclude_companies, include_docs, exclude_docs : various
        Default filters for searches.

    Methods
    -------
    search(question, ...)
        Run a single search query.
    searches(queries, ...)
        Run multiple searches concurrently and yield results.
    bulk_search(question, ...)
        Perform a bulk (slow) search query for large result sets.
    visit(html="", recrawl=False, render=False, url=None)
        Visit a URL and return structured page data.
    version()
        Retrieve the current version information for the Nosible API.
    indexed(url)
        Check if a URL has been indexed by Nosible.
    preflight(url)
        Run a preflight check for crawling/preprocessing on a URL.
    get_rate_limits()
        Get a plaintext summary of rate limits for all subscription plans.
    close()
        Close the client and release resources.
    __enter__(), __exit__()
        Context manager support for automatic cleanup.
    """

    def __init__(
        self,
        nosible_api_key: str = None,
        llm_api_key: str = None,
        openai_base_url: str = "https://openrouter.ai/api/v1",
        sentiment_model: str = "openai/gpt-4o",
        timeout: int = 30,
        retries: int = 5,
        concurrency: int = 10,
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
    ) -> None:
        """
        Initialize the Nosible client.

        Parameters
        ----------
        nosible_api_key : str, optional
            API key for the Nosible Search API.
        llm_api_key : str, optional
            API key for LLM-based query expansions.
        timeout : int, default=30
            Request timeout for HTTP calls.
        retries : int, default=5
            Number of retry attempts for transient HTTP errors.
        concurrency : int, default=10
            Maximum concurrent search requests.
        publish_start : str, optional
            Earliest publish date filter (ISO formatted date).
        publish_end : str, optional
            Latest publish date filter (ISO formatted date).
        include_netlocs : list of str, optional
            Domains to include.
        exclude_netlocs : list of str, optional
            Domains to exclude.
        visited_start : str, optional
            Earliest visit date filter (ISO formatted date).
        visited_end : str, optional
            Latest visit date filter (ISO formatted date).
        certain : bool, optional
            True if we are 100% sure of the date.
        include_languages : list of str, optional
            Language codes to include.
        exclude_languages : list of str, optional
            Language codes to exclude.
        include_companies : list of str, optional
            Google KG IDs to require.
        exclude_companies : list of str, optional
            Google KG IDs to forbid.
        openai_base_url : str, optional
            Base URL for the OpenAI API (default is OpenRouter).
        sentiment_model : str, optional
            Model to use for sentiment analysis (default is "openai/gpt-4o").

        Raises
        ------
        ValueError
            If no Nosible API key is provided.
        """
        # API Keys
        if nosible_api_key is not None:
            self.nosible_api_key = nosible_api_key
        elif os.getenv("NOSIBLE_API_KEY") is not None:
            try:
                self.nosible_api_key = os.getenv("NOSIBLE_API_KEY")
            except KeyError:
                raise ValueError("Must provide api_key or set $NOSIBLE_API_KEY")

        self.llm_api_key = llm_api_key or os.getenv("LLM_API_KEY")
        self.openai_base_url = openai_base_url
        self.sentiment_model = sentiment_model
        # Network parameters
        self.timeout = timeout
        self.retries = retries
        self.concurrency = concurrency

        # Initialize Logger
        self.logger = logging.getLogger(__name__)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        self._limiters = {
            endpoint: [RateLimiter(calls, period) for calls, period in buckets]
            for endpoint, buckets in PLAN_RATE_LIMITS[self._get_user_plan()].items()
        }

        # Define retry decorator
        self._post = retry(
            reraise=True,
            stop=stop_after_attempt(self.retries) | stop_after_delay(self.timeout),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(requests.exceptions.RequestException),
            before_sleep=before_sleep_log(self.logger, logging.WARNING),
        )(self._post)

        # Wrap _generate_expansions in the same retry logic
        self._generate_expansions = retry(
            reraise=True,
            stop=stop_after_attempt(self.retries) | stop_after_delay(self.timeout),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(Exception),
            before_sleep=before_sleep_log(self.logger, logging.WARNING),
        )(self._generate_expansions)

        # Thread pool for parallel searches
        self._session = requests.Session()
        self._executor = ThreadPoolExecutor(max_workers=self.concurrency)

        # Headers
        self.headers = {"Accept-Encoding": "gzip", "Content-Type": "application/json", "api-key": self.nosible_api_key}

        # Filters
        self.publish_start = publish_start
        self.publish_end = publish_end
        self.include_netlocs = include_netlocs
        self.exclude_netlocs = exclude_netlocs
        self.include_companies = include_companies
        self.exclude_companies = exclude_companies
        self.visited_start = visited_start
        self.visited_end = visited_end
        self.certain = certain
        self.include_languages = include_languages
        self.exclude_languages = exclude_languages
        self.include_companies = include_companies
        self.exclude_companies = exclude_companies
        self.exclude_docs = exclude_docs
        self.include_docs = include_docs

    def search(
        self,
        *,
        search: Search = None,
        question: str = None,
        expansions: list[str] = None,
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
        include_docs: list = None,
        exclude_docs: list = None,
    ) -> ResultSet:
        """
        Run a single search query.

        If `question` is a string, it is wrapped into a Search with the provided
        parameters; if it is already a Search instance, its fields take precedence.

        Parameters
        ----------
        question : str
            Query string.
        search : Search
            Search object to search with.
        expansions : list of str, optional
            List of LLM‐generated expansions.
        sql_filter : list of str, optional
            SQL‐style filter clauses.
        n_results : int, default=100
            Max number of results (max 100).
        n_probes : int, default=30
            Number of index shards to probe.
        n_contextify : int, default=128
            Context window size per result.
        algorithm : str, default="hybrid-2"
            Search algorithm type.
        publish_start : str, optional
            Earliest publish date filter (ISO formatted date).
        publish_end : str, optional
            Latest publish date filter (ISO formatted date).
        include_netlocs : list of str, optional
            Domains to include.
        exclude_netlocs : list of str, optional
            Domains to exclude.
        visited_start : str, optional
            Earliest visit date filter (ISO formatted date).
        visited_end : str, optional
            Latest visit date filter (ISO formatted date).
        certain : bool, optional
            True if we are 100% sure of the date.
        include_languages : list of str, optional
            Language codes to include.
        exclude_languages : list of str, optional
            Language codes to exclude.
        include_companies : list of str, optional
            Google KG IDs to require.
        exclude_companies : list of str, optional
            Google KG IDs to forbid.
        include_docs : list of str, optional
            URL hashes of docs to include.
        exclude_docs : list of str, optional
            URL hashes of docs to exclude.

        Returns
        -------
        ResultSet
            The results of the search.

        Raises
        ------
        TypeError
            If both question and search are specified
        TypeError
            If neither question nor search are specified
        ValueError
            If `n_results` > 100.

        Notes
        -----
        You must provide either a `question` string or a `Search` object, not both.
        The search parameters will be set from the provided object or string and any additional keyword arguments.

        Examples
        --------
        >>> from nosible.classes.search import Search
        >>> from nosible import Nosible
        >>> s = Search(question="OpenAI", n_results=10)
        >>> with Nosible() as nos:
        ...     results = nos.search(search=s)
        ...     print(isinstance(results, ResultSet))
        ...     print(len(results))
        True
        10
        """
        if (question is None and search is None) or (question is not None and search is not None):
            raise TypeError("Specify exactly one of 'question' or 'search'.")

        search_obj = self._construct_search(
            question=search if search is not None else question,
            expansions=expansions,
            sql_filter=sql_filter,
            n_results=n_results,
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

        return self._executor.submit(self._search_single, search_obj).result()

    def searches(
        self,
        *,
        questions: list[str] = None,
        searches: Union[SearchSet, list[Search]] = None,
        expansions: list[str] = None,
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
        include_docs: list = None,
        exclude_docs: list = None,
    ) -> Iterator[ResultSet]:
        """
        Run multiple searches concurrently and yield results.

        Parameters
        ----------
        queries : list of str
            The search queries to execute.
        searches: SearchSet or list of Search
            The searches execute.
        expansions : list of str, optional
            List of expansion terms to use for each search.
        sql_filter : list of str, optional
            SQL-like filters to apply to the search.
        n_results : int, default=100
            Number of results to return per search.
        n_probes : int, default=30
            Number of probes to use for the search algorithm.
        n_contextify : int, default=128
            Context window size for the search.
        algorithm : str, default="hybrid-2"
            Search algorithm to use.
        publish_start : str, optional
            Filter results published after this date (ISO formatted date).
        publish_end : str, optional
            Filter results published before this date (ISO formatted date).
        include_netlocs : list of str, optional
            Only include results from these domains.
        exclude_netlocs : list of str, optional
            Exclude results from these domains.
        visited_start : str, optional
            Only include results visited after this date (ISO formatted date).
        visited_end : str, optional
            Only include results visited before this date (ISO formatted date).
        certain : bool, optional
            Only include results with high certainty.
        include_languages : list of str, optional
            Only include results in these languages.
        exclude_languages : list of str, optional
            Exclude results in these languages.
        include_companies : list of str, optional
            Only include results from these companies.
        exclude_companies : list of str, optional
            Exclude results from these companies.
        include_netlocs : list of str, optional
            Only include results from these domains.
        exclude_netlocs : list of str, optional
            Exclude results from these domains.

        Yields
        ------
        ResultSet or None
            Each completed search’s results, or None on failure.

        Raises
        ------
        TypeError
            If `queries` is not a list of strings, a list of Search objects, or a SearchSet instance.
        TypeError
            If both queries and searches are specified.
        TypeError
            If neither queries nor searches are specified.

        Notes
        -----
        You must provide either a list of `questions` or a list of `Search` objects, not both.
        The search parameters will be set from the provided object or string and any additional keyword arguments.

        Examples
        --------
        >>> from nosible import Nosible
        >>> queries = SearchSet(
        ...     [Search(question="OpenAI", n_results=5), Search(question="Python programming", n_results=5)]
        ... )
        >>> with Nosible() as nos:
        ...     results_list = list(nos.searches(searches=queries))
        >>> print(len(results_list))
        2
        >>> for r in results_list:
        ...     print(isinstance(r, ResultSet), bool(r))
        True True
        True True
        """
        if (questions is None and searches is None) or (questions is not None and searches is not None):
            raise TypeError("Specify exactly one of 'questions' or 'searches'.")

        search_queries = questions if questions is not None else searches

        searches_list = self._construct_search(
            question=search_queries,
            expansions=expansions,
            sql_filter=sql_filter,
            n_results=n_results,
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

        # Submit all searches concurrently
        future_to_search = {self._executor.submit(self._search_single, s): s for s in searches_list}

        # Yield results as they complete
        for future in as_completed(future_to_search):
            try:
                yield future.result()
            except Exception as e:
                failed = future_to_search[future]  # TODO This can throw an error.
                self.logger.warning(f"Search for {failed.question!r} failed: {e}")
                yield None

    @_rate_limited("fast")
    def _search_single(self, search_obj: Search) -> ResultSet:
        """
        Execute a single search request using the parameters from a Search object.

        Parameters
        ----------
        search_obj : Search
            A Search instance containing all search parameters.

        Returns
        -------
        ResultSet
            The results of the search.

        Raises
        ------
        ValueError
            If `n_results` > 100.
        """
        # --------------------------------------------------------------------------------------------------------------
        # Setting search params. Individual search will overide Nosible defaults.
        # --------------------------------------------------------------------------------------------------------------
        question = search_obj.question  # No default
        expansions = search_obj.expansions if search_obj.expansions is not None else []  # Default to empty list
        sql_filter = search_obj.sql_filter if search_obj.sql_filter is not None else None
        n_results = search_obj.n_results if search_obj.n_results is not None else 100
        n_probes = search_obj.n_probes if search_obj.n_probes is not None else 30
        n_contextify = search_obj.n_contextify if search_obj.n_contextify is not None else 128
        algorithm = search_obj.algorithm if search_obj.algorithm is not None else "hybrid-2"
        publish_start = search_obj.publish_start if search_obj.publish_start is not None else self.publish_start
        publish_end = search_obj.publish_end if search_obj.publish_end is not None else self.publish_end
        include_netlocs = search_obj.include_netlocs if search_obj.include_netlocs is not None else self.include_netlocs
        exclude_netlocs = search_obj.exclude_netlocs if search_obj.exclude_netlocs is not None else self.exclude_netlocs
        visited_start = search_obj.visited_start if search_obj.visited_start is not None else self.visited_start
        visited_end = search_obj.visited_end if search_obj.visited_end is not None else self.visited_end
        certain = search_obj.certain if search_obj.certain is not None else self.certain
        include_languages = (
            search_obj.include_languages if search_obj.include_languages is not None else self.include_languages
        )
        exclude_languages = (
            search_obj.exclude_languages if search_obj.exclude_languages is not None else self.exclude_languages
        )
        include_companies = (
            search_obj.include_companies if search_obj.include_companies is not None else self.include_companies
        )
        exclude_companies = (
            search_obj.exclude_companies if search_obj.exclude_companies is not None else self.exclude_companies
        )

        # Generate expansions if not provided
        if expansions is None:
            expansions = []
        # Generate sql_filter if not provided
        if sql_filter is None:
            sql_filter = self._format_sql(
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

        # Enforce limits
        if n_results > 100:
            raise ValueError("Search can not have more than 100 results - Use bulk search instead.")
        filter_responses = n_results
        n_results = max(n_results, 10)

        payload = {
            "question": question,
            "expansions": expansions,
            "sql_filter": sql_filter,
            "n_results": n_results,
            "n_probes": n_probes,
            "n_contextify": n_contextify,
            "algorithm": algorithm,
        }

        resp = self._post(url="https://www.nosible.ai/search/v1/fast-search", payload=payload)
        resp.raise_for_status()
        items = resp.json().get("response", [])[:filter_responses]
        return ResultSet.from_dicts(items)

    @staticmethod
    def _construct_search(
        question: Union[str, Search, SearchSet, list[Search], list[str]], **options
    ) -> Union[Search, SearchSet]:
        """
        Constructs a `Search` or `SearchSet` object from the provided input.
        Parameters
        ----------
        question : Union[str, Search, SearchSet, list[Search], list[str]]
            The input to construct the search from. This can be a single search query string,
            a `Search` object, a `SearchSet` object, or a list of either search query strings or `Search` objects.
        **options
            Additional keyword arguments to pass to the `Search` initializer.
        Returns
        -------
        Union[Search, SearchSet]
            A `Search` object if the input is a single query or `Search`, or a `SearchSet` object if the input is a
            list or a `SearchSet`.
        Raises
        ------
        TypeError
            If `question` is not a `str`, `Search`, `SearchSet`, or a list of these types.
        Notes
        -----
        All extra parameters are passed through to the `Search` initializer.
        """

        def make_search(q: Union[str, Search]) -> Search:
            return q if isinstance(q, Search) else Search(question=q, **options)

        if isinstance(question, SearchSet):
            return question
        if isinstance(question, Search):
            return question
        if isinstance(question, list):
            return SearchSet([make_search(q) for q in question])
        if isinstance(question, str):
            return make_search(question)

        raise TypeError("`question` must be str, Search, SearchSet, or a list thereof")

    @_rate_limited("slow")
    def bulk_search(
        self,
        *,
        search: Search = None,
        question: str = None,
        expansions: list[str] = None,
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
        include_docs: list = None,
        exclude_docs: list = None,
    ) -> ResultSet:
        """
        Perform a bulk (slow) search query (1,000–10,000 results) against the Nosible API.

        Parameters
        ----------
        question : str or None
            Query string. Provide either a question string or a Search object.
        search : Search or None
            Search object to search with. Provide either a Search object or a question string.
        expansions : list of str, optional
            Optional list of expanded query strings.
        sql_filter : list of str, optional
            Optional SQL WHERE clause filters.
        n_results : int, default=100
            Number of results per query (1,000–10,000).
        n_probes : int, default=30
            Number of shards to probe.
        n_contextify : int, default=128
            Context window size per result.
        algorithm : str, default="hybrid-2"
            Search algorithm identifier.
        publish_start : str, optional
            Filter for earliest publish date.
        publish_end : str, optional
            Filter for latest publish date.
        include_netlocs : list of str, optional
            Domains to include.
        exclude_netlocs : list of str, optional
            Domains to exclude.
        visited_start : str, optional
            Filter for earliest visit date.
        visited_end : str, optional
            Filter for latest visit date.
        certain : bool, optional
            True if we are 100% sure of the date.
        include_languages : list of str, optional
            Languages to include.
        exclude_languages : list of str, optional
            Languages to exclude.
        include_companies : list of str, optional
            Company IDs to require.
        exclude_companies : list of str, optional
            Company IDs to forbid.
        include_docs : list of str, optional
            URL hashes of documents to include.
        exclude_docs : list of str, optional
            URL hashes of documents to exclude.

        Returns
        -------
        ResultSet
            The results of the bulk search.

        Raises
        ------
        ValueError
            If `n_results` is out of bounds (<100 or >10000).
        TypeError
            If both question and search are specified.
        TypeError
            If neither question nor search are specified.

        Notes
        -----
        You must provide either a `question` string or a `Search` object, not both.
        The search parameters will be set from the provided object or string and any additional keyword arguments.

        Examples
        --------
        >>> # initialize and use with context manager
        >>> with Nosible(include_netlocs=["bbc.com"]) as nos:  # doctest: +SKIP
        ...     results = nos.bulk_search(question="OpenAI", n_results=2000)  # doctest: +SKIP
        ...     print(isinstance(results, ResultSet))  # doctest: +SKIP
        ...     print(len(results))  # doctest: +SKIP
        True
        2000
        """
        if question is not None and search is not None:
            raise TypeError("Question and search cannot be both specified")

        if question is None and search is None:
            raise TypeError("Either question or search must be specified")

        # If a Search object is provided, extract its fields
        if search is not None:
            question = search.question
            expansions = search.expansions if search.expansions is not None else expansions
            sql_filter = search.sql_filter if search.sql_filter is not None else sql_filter
            n_results = search.n_results if search.n_results is not None else n_results
            n_probes = search.n_probes if search.n_probes is not None else n_probes
            n_contextify = search.n_contextify if search.n_contextify is not None else n_contextify
            algorithm = search.algorithm if search.algorithm is not None else algorithm
            publish_start = search.publish_start if search.publish_start is not None else publish_start
            publish_end = search.publish_end if search.publish_end is not None else publish_end
            include_netlocs = search.include_netlocs if search.include_netlocs is not None else include_netlocs
            exclude_netlocs = search.exclude_netlocs if search.exclude_netlocs is not None else exclude_netlocs
            visited_start = search.visited_start if search.visited_start is not None else visited_start
            visited_end = search.visited_end if search.visited_end is not None else visited_end
            certain = search.certain if search.certain is not None else certain
            include_languages = search.include_languages if search.include_languages is not None else include_languages
            exclude_languages = search.exclude_languages if search.exclude_languages is not None else exclude_languages
            include_companies = search.include_companies if search.include_companies is not None else include_companies
            exclude_companies = search.exclude_companies if search.exclude_companies is not None else exclude_companies
            include_docs = search.include_docs if search.include_docs is not None else include_docs
            exclude_docs = search.exclude_docs if search.exclude_docs is not None else exclude_docs

        # Default expansions and filters
        if expansions is None:
            expansions = self._generate_expansions(question=question)
        # Generate sql_filter if unset
        if sql_filter is None:
            sql_filter = self._format_sql(
                publish_start=publish_start if publish_start is not None else self.publish_start,
                publish_end=publish_end if publish_end is not None else self.publish_end,
                include_netlocs=include_netlocs if include_netlocs is not None else self.include_netlocs,
                exclude_netlocs=exclude_netlocs if exclude_netlocs is not None else self.exclude_netlocs,
                visited_start=visited_start if visited_start is not None else self.visited_start,
                visited_end=visited_end if visited_end is not None else self.visited_end,
                certain=certain if certain is not None else self.certain,
                include_languages=include_languages if include_languages is not None else self.include_languages,
                exclude_languages=exclude_languages if exclude_languages is not None else self.exclude_languages,
                include_companies=include_companies if include_companies is not None else self.include_companies,
                exclude_companies=exclude_companies if exclude_companies is not None else self.exclude_companies,
                include_docs=include_docs if include_docs is not None else self.include_docs,
                exclude_docs=exclude_docs if exclude_docs is not None else self.exclude_docs,
            )

        self.logger.debug(f"SQL Filter: {sql_filter}")

        # Validate n_result bounds
        if n_results <= 100:
            raise ValueError(
                "Bulk search must have at least 100 results per query; use search() for smaller result sets."
            )
        if n_results > 10000:
            raise ValueError("Bulk search cannot have more than 10000 results per query.")

        # Enforce Minimums
        filter_responses = n_results
        # slow search must ask for at least 1 000
        n_results = max(n_results, 1000)

        payload = {
            "question": question,
            "expansions": expansions,
            "sql_filter": sql_filter,
            "n_results": n_results,
            "n_probes": n_probes,
            "n_contextify": n_contextify,
            "algorithm": algorithm,
        }
        resp = self._post(url="https://www.nosible.ai/search/v1/slow-search", payload=payload)
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            raise ValueError(f"[{question!r}] HTTP {resp.status_code}: {resp.text}") from e

        data = resp.json()

        # Slow search: download & decrypt
        download_from = data.get("download_from")
        if ".zstd." in download_from:
            download_from = download_from.replace(".zstd.", ".gzip.", 1)
        decrypt_using = data.get("decrypt_using")
        for _ in range(100):
            dl = self._session.get(download_from, timeout=self.timeout)
            if dl.ok:
                fernet = Fernet(decrypt_using.encode())
                decrypted = fernet.decrypt(dl.content)
                decompressed = gzip.decompress(decrypted)
                api_resp = json_loads(decompressed)
                return ResultSet.from_dicts(api_resp.get("response", [])[:filter_responses])
            time.sleep(10)
        raise ValueError("Results were not retrieved from Nosible")

    @_rate_limited("visit")
    def visit(self, html: str = "", recrawl: bool = False, render: bool = False, url: str = None) -> WebPageData:
        """
        Visit a given URL and return a structured WebPageData object for the page.

        Parameters
        ----------
        html : str, default=""
            Raw HTML to process instead of fetching.
        recrawl : bool, default=False
            If True, force a fresh crawl.
        render : bool, default=False
            If True, allow JavaScript rendering before extraction.
        url : str, default=None
            The URL to fetch and parse.

        Returns
        -------
        WebPageData
            Structured page data object.

        Raises
        ------
        TypeError
            If URL is not provided.

        Examples
        --------
        >>> from nosible import Nosible  # doctest: +SKIP
        >>> with Nosible() as nos:  # doctest: +SKIP
        ...     out = nos.visit(url="https://www.dailynewsegypt.com/2023/09/08/g20-and-its-summits/")  # doctest: +SKIP
        ...     print(isinstance(out, type(WebPageData)))  # doctest: +SKIP
        ...     print(hasattr(out, "languages"))  # doctest: +SKIP
        ...     print(hasattr(out, "page"))  # doctest: +SKIP
        True
        True
        True
        """
        # self._enforce("visit")
        if url is None:
            raise TypeError("URL must be provided")
        response = self._post(
            url="https://www.nosible.ai/search/v1/visit",
            payload={"html": html, "recrawl": recrawl, "render": render, "url": url},
        )
        try:
            data = response.json()
        except Exception as e:
            self.logger.error(f"Failed to parse JSON from response: {e}")
            raise ValueError("Invalid JSON response from server") from e

        if "response" not in data:
            self.logger.error(f"No 'response' key in server response: {data}")
            raise ValueError("No 'response' key in server response")

        response_data = data["response"]
        return WebPageData(
            languages=response_data["languages"],
            metadata=response_data["metadata"],
            page=response_data["page"],
            request=response_data["request"],
            snippets=response_data["snippets"],
            statistics=response_data["statistics"],
            structured=response_data["structured"],
            url_tree=response_data["url_tree"],
        )

    def version(self) -> str:
        """
        Retrieve the current version information for the Nosible API.

        Returns
        -------
        str
            JSON-formatted string containing API version details.

        Examples
        --------
        >>> import json
        >>> from nosible import Nosible
        >>> with Nosible() as nos:
        ...     v = nos.version()
        ...     data = json.loads(v)
        ...     # top‐level object must be a dict
        ...     print(isinstance(data, dict))
        ...     # must have a "response" key mapping to another dict
        ...     print("response" in data and isinstance(data["response"], dict))
        ...     # that inner dict must have exactly the expected sub-keys
        ...     expected = {
        ...         "database",
        ...         "date",
        ...         "documents",
        ...         "runtime",
        ...         "snippets",
        ...         "time",
        ...         "tokens",
        ...         "version",
        ...         "words",
        ...     }
        ...     print(set(data["response"].keys()) == expected)
        True
        True
        True
        """
        response = self._post(url="https://www.nosible.ai/search/v1/version", payload={})

        return json.dumps(response.json(), indent=2, sort_keys=True)

    def indexed(self, url: str = None) -> bool:
        """
        This function checks if a URL has been indexed by Nosible.

        Parameters
        ----------
        url : str, optional
            The full URL to verify.

        Returns
        -------
        bool
            True if the URL is in the index.
            False if the URL is not in the index.

        Raises
        ------
        ValueError
            If the API returns an unexpected message.
        requests.HTTPError
            If the HTTP request fails.

        Examples
        --------
        >>> from nosible import Nosible
        >>> with Nosible() as nos:
        ...     idx = nos.indexed(url="https://www.dailynewsegypt.com/2023/09/08/g20-and-its-summits/")
        ...     print(idx)
        True
        """
        response = self._post(url="https://www.nosible.ai/search/v1/indexed", payload={"url": url})

        response.raise_for_status()
        data = response.json()
        msg = data.get("message")
        if msg == "The URL is in the system.":
            return True
        if msg == "The URL is nowhere to be found.":
            return False
        raise ValueError(f"Unexpected response from indexed endpoint: {data!r}")

    def preflight(self, url: str = None) -> str:
        """
        Run a preflight check for crawling/preprocessing on a URL.

        Parameters
        ----------
        url : str, optional
            The URL to validate or prepare for indexing.

        Returns
        -------
        str
            JSON-formatted string with errors, warnings, or recommendations.

        Examples
        --------
        >>> from nosible import Nosible
        >>> with Nosible() as nos:
        ...     pf = nos.preflight(url="https://www.dailynewsegypt.com/2023/09/08/g20-and-its-summits/")
        ...     print(pf)
        {
          "response": {
            "domain": "dailynewsegypt",
            "fragment": "",
            "geo": "US",
            "hash": "ENNmqkF1mGNhVhvhmbUEs4U2",
            "netloc": "www.dailynewsegypt.com",
            "path": "/2023/09/08/g20-and-its-summits/",
            "prefix": "www",
            "proxy": "US",
            "query": "",
            "query_allowed": {},
            "query_blocked": {},
            "raw_url": "https://www.dailynewsegypt.com/2023/09/08/g20-and-its-summits/",
            "scheme": "https",
            "suffix": "com",
            "url": "https://www.dailynewsegypt.com/2023/09/08/g20-and-its-summits"
          }
        }
        """
        response = self._post(url="https://www.nosible.ai/search/v1/preflight", payload={"url": url})

        return json.dumps(response.json(), indent=2, sort_keys=True)

    def get_rate_limits(self) -> str:
        """
        Generate a plaintext summary of rate limits for every subscription plan.

        Returns
        -------
        str
            A multi-line string containing rate limits for each plan.

        Examples
        --------
        >>> nos = Nosible(nosible_api_key="test|xyz")  # doctest: +SKIP
        >>> print(nos.get_rate_limits())  # doctest: +SKIP
        Free (Your current plan)
        | Endpoint    | Per Month | Per Day | Per Minute |
        | ----------- | --------- | ------- | ---------- |
        | Fast Search |     3 000 |     100 |         10 |
        | URL Visits  |       300 |      10 |          1 |
        | Slow Search |       300 |      10 |          1 |

        Basic
        | Endpoint    | Per Month | Per Day | Per Minute |
        ...
        """
        # Human-friendly plan names
        display = {
            "test": "Free",
            "basic": "Basic",
            "pro": "Pro",
            "pro+": "Pro+",
            "bus": "Business",
            "bus+": "Business+",
            "ent": "Enterprise",
        }

        # Human-friendly endpoint names
        endpoint_name = {"fast": "Fast Search", "visit": "URL Visits", "slow": "Bulk Search"}

        out = [
            "Below are the rate limits for all NOSIBLE plans.",
            "To upgrade your package, visit https://www.nosible.ai/products.\n",
        ]

        user_plan = self._get_user_plan()
        current_plan = ""

        # Preserve the order you care about:
        for plan in ["test", "basic", "pro", "pro+", "bus", "bus+", "ent"]:
            name = display.get(plan, plan)
            if plan == user_plan:
                current_plan = " (Your current plan)"

            out.append(f"{name}:{current_plan}")
            out.append("| Endpoint    | Per Month | Per Day | Per Minute |")
            out.append("| ----------- | --------- | ------- | ---------- |")

            for ep in ["fast", "visit", "slow"]:
                buckets = PLAN_RATE_LIMITS[plan][ep]
                # Find minute & day
                minute = next(limit for limit, i in buckets if i == 60)
                day = next(limit for limit, i in buckets if i == 24 * 3600)
                month = day * 30
                out.append(f"| {endpoint_name[ep]:<11} | {month:>9} | {day:>7} | {minute:>10} |")

            out.append("")  # Blank line
            current_plan = ""

        return "\n".join(out)

    def close(self):
        """
        Close the Nosible client, shutting down the HTTP session
        and thread pool to release network and threading resources.

        Returns
        -------
        None

        Examples
        --------
        >>> from nosible import Nosible
        >>> nos = Nosible()
        >>> result = nos.close()
        >>> print(result is None)
        True
        >>> # Calling close again should be a no-op
        >>> nos.close()
        >>> print("No Error")
        No Error
        """
        # Shut down HTTP session
        try:
            self._session.close()
        except Exception:
            pass
        # Shut down thread pool
        try:
            # wait = True ensures all submitted tasks complete or are cancelled
            self._executor.shutdown(wait=True)
        except Exception:
            pass

    def _post(self, url: str, payload: dict, headers: dict = None, timeout: int = None) -> requests.Response:
        """
        Internal helper to send a POST request with retry logic.

        Parameters
        ----------
        url : str
            Endpoint URL.
        payload : dict
            JSON-serializable payload.
        headers : dict, optional
            Override headers for this request.
        timeout : int, optional
            Override timeout for this request.

        Returns
        -------
        requests.Response
            The HTTP response object.
        """
        return self._session.post(
            url=url,
            json=payload,
            headers=headers if headers is not None else self.headers,
            timeout=timeout if timeout is not None else self.timeout,
        )

    def _get_user_plan(self) -> str:
        """
        Determine the user's subscription plan from the API key.

        The `nosible_api_key` is expected to start with a plan prefix followed by
        a pipe (`|`) and any additional data. This method splits on the first
        pipe character, validates the prefix against supported plans, and returns it.

        Returns
        -------
        str
            The plan you are currently on.

        Raises
        ------
        ValueError
            If the extracted prefix is not one of the recognized plan names.
        """
        # Split off anything after the first '|'
        prefix = (self.nosible_api_key or "").split("|", 1)[0]

        # Map prefixes -> human-friendly plan names
        plans = {"test", "basic", "pro", "pro+", "bus", "bus+", "ent"}

        if prefix not in plans:
            raise ValueError(f"{prefix} is not a valid plan prefix.")

        return prefix

    def _generate_expansions(self, question: Union[str, Search]) -> list:
        """
        Generate up to 10 semantically diverse question expansions using an LLM.

        Parameters
        ----------
        question : str
            Original user query.

        Returns
        -------
        list of str
            Up to 10 expanded query strings.

        Raises
        ------
        ValueError
            If no LLM API key is set.
        RuntimeError
            If the LLM response is invalid or cannot be parsed.
        """
        if not self.llm_api_key:
            raise ValueError("LLM API key is required for generating expansions.")

        # If the user put in a search, get the question out of it.
        if isinstance(question, Search):
            question = question.question

        # Build a clear prompt that demands JSON output of exactly 10 strings.
        prompt = f"""
            # TASK DESCRIPTION

            Given a search question you must generate a list of 10 similar questions that have the same exact
            semantic meaning but are contextually and lexically different to improve search recall.

            ## Question

            Here is the question you must generate expansions for:

            Question: {question}

            # RESPONSE FORMAT

            Your response must be a JSON object structured as follows: a list of ten strings. Each string must
            be a grammatically correct question that expands on the original question to improve recall.

            [
                string,
                string,
                string,
                string,
                string,
                string,
                string,
                string,
                string,
                string
            ]

            # EXPANSION GUIDELINES

            1. **Use specific named entities** - To improve the quality of your search results you must mention
               specific named entities (people, locations, organizations, products, places) in expansions.

            2. **Expansions must be highly targeted** - To improve the quality of search results each expansion
               must be semantically unambiguous. Questions must be use between ten and fifteen words.

            3. **Expansions must improve recall** - When expanding the question leverage semantic and contextual
               expansion to maximize the ability of the search engine to find semantically relevant documents:

               - Semantic Example: Swap "climate change" with "global warming" or "environmental change".
               - Contextual Example: Swap "diabetes treatment" with "insulin therapy" or "blood sugar management".

        """.replace("                ", "")

        client = OpenAI(base_url=self.openai_base_url, api_key=self.llm_api_key)

        # Call the chat completions endpoint.
        resp = client.chat.completions.create(
            model=self.sentiment_model, messages=[{"role": "user", "content": prompt.strip()}], temperature=0.7
        )

        raw = resp.choices[0].message.content

        # Strip any leading/trailing markdown ``` or text.
        if raw.startswith("```"):
            # remove ```json ... ```
            raw = raw.strip("`").strip()
            # remove optional leading "json"
            if raw.lower().startswith("json"):
                raw = raw[len("json") :].strip()

        # Parse JSON.
        try:
            expansions = json.loads(raw)
        except Exception as decode_err:
            raise RuntimeError(f"OpenRouter response was not valid JSON: '{raw}'") from decode_err

        # Validate.
        if not isinstance(expansions, list) or len(expansions) != 10 or not all(isinstance(q, str) for q in expansions):
            raise RuntimeError("Invalid response: 'choices' missing or empty")

        self.logger.debug(f"Successful expansions: {expansions}")
        return expansions

    def _format_sql(
        self,
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
    ) -> str:
        """
        Construct an SQL SELECT statement with WHERE clauses based on provided filters.

        Parameters
        ----------
        publish_start : str, optional
            Earliest published date filter.
        publish_end : str, optional
            Latest published date filter.
        include_netlocs : list of str, optional
            Domains to whitelist.
        exclude_netlocs : list of str, optional
            Domains to blacklist.
        visited_start : str, optional
            Earliest visit date filter.
        visited_end : str, optional
            Latest visit date filter.
        certain : bool, optional
            True if we are 100% sure of the date.
        include_languages : list of str, optional
            Languages to include.
        exclude_languages : list of str, optional
            Languages to exclude.
        include_companies : list of str, optional
            Company IDs to require.
        exclude_companies : list of str, optional
            Company IDs to forbid.
        include_docs : list of str, optional
            URL hashes of documents to include.
        exclude_docs : list of str, optional
            URL hashes of documents to exclude.

        Returns
        -------
        str
            An SQL query string with appropriate WHERE clauses.
        """
        sql = ["SELECT loc FROM engine"]
        clauses: list[str] = []

        # published date range
        if publish_start or publish_end:
            if publish_start and publish_end:
                clauses.append(f"published >= '{publish_start}' AND published <= '{publish_end}'")
            elif publish_start:
                clauses.append(f"published >= '{publish_start}'")
            else:  # only publish_end
                clauses.append(f"published <= '{publish_end}'")

        # visited date range
        if visited_start or visited_end:
            if visited_start and visited_end:
                clauses.append(f"visited >= '{visited_start}' AND visited <= '{visited_end}'")
            elif visited_start:
                clauses.append(f"visited >= '{visited_start}'")
            else:  # only visited_end
                clauses.append(f"visited <= '{visited_end}'")

        # date certainty filter
        if certain is True:
            clauses.append("certain = TRUE")
        elif certain is False:
            clauses.append("certain = FALSE")

        # include / exclude netlocs
        if include_netlocs:
            in_list = ", ".join(f"'{n}'" for n in include_netlocs)
            clauses.append(f"netloc IN ({in_list})")
        if exclude_netlocs:
            ex_list = ", ".join(f"'{n}'" for n in exclude_netlocs)
            clauses.append(f"netloc NOT IN ({ex_list})")

        # include / exclude languages
        if include_languages:
            langs = ", ".join(f"'{lang}'" for lang in include_languages)
            clauses.append(f"language IN ({langs})")
        if exclude_languages:
            langs = ", ".join(f"'{lang}'" for lang in exclude_languages)
            clauses.append(f"language NOT IN ({langs})")

        # include companies (assign each to a company_N column)
        if include_companies:
            for idx, gkg_id in enumerate(include_companies, start=1):
                clauses.append(f"company_{idx} = '{gkg_id}'")

        # exclude companies (none of the company_N columns may match)
        if exclude_companies:
            gkg_ids = ", ".join(f"'{c}'" for c in exclude_companies)
            # assume up to 3 company columns; adjust if you support more
            clauses.append(" AND ".join(f"company_{i} NOT IN ({gkg_ids})" for i in range(1, 4)))

        if include_docs:
            # assume these are URL hashes, e.g. "ENNmqkF1mGNhVhvhmbUEs4U2"
            doc_hashes = ", ".join(f"'{doc}'" for doc in include_docs)
            clauses.append(f"doc_hash IN ({doc_hashes})")

        if exclude_docs:
            # assume these are URL hashes, e.g. "ENNmqkF1mGNhVhvhmbUEs4U2"
            doc_hashes = ", ".join(f"'{doc}'" for doc in exclude_docs)
            clauses.append(f"doc_hash NOT IN ({doc_hashes})")

        # join everything
        if clauses:
            sql.append("WHERE " + " AND ".join(clauses))

        sql_filter = " ".join(sql)

        # Validate the SQL query against the schemas
        if not self._validate_sql(sql_filter):
            raise ValueError(f"Invalid SQL query: {sql_filter!r}. Please check your filters and try again.")

        self.logger.debug(f"Generated SQL filter: {sql_filter}")
        # Return the final SQL filter string
        return sql_filter

    def _validate_sql(self, sql: str) -> bool:
        """
        Validate a SQL query string by attempting to execute it against a mock schema.

        Parameters
        ----------
        sql : str
            The SQL query string to validate.

        Returns
        -------
        bool
            True if the SQL is valid, False otherwise.

        Examples
        --------
        >>> Nosible()._validate_sql(sql="SELECT 1")
        True
        >>> Nosible()._validate_sql(sql="SELECT * FROM missing_table")
        False
        """
        # Define a mock schema for the 'engine' table with all possible columns used in _format_sql
        columns = [
            "loc",
            "published",
            "visited",
            "certain",
            "netloc",
            "language",
            "company_1",
            "company_2",
            "company_3",
            "doc_hash",
        ]
        # Create a dummy DataFrame with correct columns and no rows
        df = pl.DataFrame({col: [] for col in columns})
        ctx = SQLContext()
        ctx.register("engine", df)
        try:
            ctx.execute(sql)
            return True
        except Exception:
            return False

    def __enter__(self):
        """
        Enter the context manager, returning this client instance.

        Returns
        -------
        Nosible
            The current client instance.
        """
        return self

    def __exit__(self, exc_type: type, exc: Exception, tb: traceback):
        """
        Exit the context manager, ensuring cleanup of resources.

        Parameters
        ----------
        exc_type : type or None
            Exception type if raised.
        exc : Exception or None
            Exception instance if raised.
        tb : traceback or None
            Traceback if exception was raised.

        Returns
        -------
        None
        """
        self.close()

    def __del__(self):
        """
        Destructor to ensure resources are cleaned up if not explicitly closed.

        Returns
        -------
        None
        """
        # Ensure it's called
        self.close()
