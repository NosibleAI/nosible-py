import gzip
import json
import logging
import os
import re
import sys
import textwrap
import time
import types
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional, Union

import httpx
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
from nosible.classes.snippet_set import SnippetSet
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

    Parameters
    ----------
    nosible_api_key : str, optional
        API key for the Nosible Search API.
    llm_api_key : str, optional
        API key for LLM-based query expansions.
    openai_base_url : str
        Base URL for the OpenAI-compatible LLM API. (default is OpenRouter's API endpoint)
    sentiment_model : str, optional
        Model to use for sentiment analysis (default is "openai/gpt-4o").
    expansions_model : str, optional
        Model to use for expansions (default is "openai/gpt-4o").
    timeout : int
        Request timeout for HTTP calls.
    retries : int,
        Number of retry attempts for transient HTTP errors.
    concurrency : int,
        Maximum concurrent search requests.
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

    Notes
    -----
    - The `nosible_api_key` is required to access the Nosible Search API.
    - The `llm_api_key` is optional and used for LLM-based query expansions.
    - The `openai_base_url` defaults to OpenRouter's API endpoint.
    - The `sentiment_model` is used for sentiment analysis.
    - The `expansions_model` is used for generating query expansions.
    - The `timeout`, `retries`, and `concurrency` parameters control the behavior of HTTP requests.

    Examples
    --------
    >>> from nosible import Nosible  # doctest: +SKIP
    >>> nos = Nosible(nosible_api_key="your_api_key_here")  # doctest: +SKIP
    >>> search = nos.search(question="What is Nosible?", n_results=5)  # doctest: +SKIP
    """

    def __init__(
        self,
        nosible_api_key: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        openai_base_url: str = "https://openrouter.ai/api/v1",
        sentiment_model: str = "openai/gpt-4o",
        expansions_model: str = "openai/gpt-4o",
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
        # API Keys
        if nosible_api_key is not None:
            self.nosible_api_key = nosible_api_key
        elif os.getenv("NOSIBLE_API_KEY") is not None:
            try:
                self.nosible_api_key = os.getenv("NOSIBLE_API_KEY")
            except KeyError:
                raise ValueError("Must provide api_key or set $NOSIBLE_API_KEY")
        else:
            # Neither passed in nor in the environment
            raise ValueError("Must provide api_key or set $NOSIBLE_API_KEY")

        self.llm_api_key = llm_api_key or os.getenv("LLM_API_KEY")
        self.openai_base_url = openai_base_url
        self.sentiment_model = sentiment_model
        self.expansions_model = expansions_model
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
            retry=retry_if_exception_type(httpx.RequestError),
            before_sleep=before_sleep_log(self.logger, logging.WARNING),
        )(self._post)

        # Wrap _generate_expansions in the same retry logic
        self._generate_expansions = retry(
            reraise=True,
            stop=stop_after_attempt(self.retries) | stop_after_delay(self.timeout),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(httpx.RequestError),
            before_sleep=before_sleep_log(self.logger, logging.WARNING),
        )(self._generate_expansions)

        # Thread pool for parallel searches
        self._session = httpx.Client(follow_redirects=True)
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
        search: Search = None,
        question: str = None,
        expansions: list[str] = None,
        sql_filter: list[str] = None,
        n_results: int = 100,
        n_probes: int = 30,
        n_contextify: int = 128,
        algorithm: str = "hybrid-2",
        min_similarity: float = None,
        must_include: list[str] = None,
        must_exclude: list[str] = None,
        autogenerate_expansions: bool = False,
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
        n_results : int
            Max number of results (max 100).
        n_probes : int
            Number of index shards to probe.
        n_contextify : int
            Context window size per result.
        algorithm : str
            Search algorithm type.
        min_similarity : float
            Results must have at least this similarity score.
        must_include : list of str
            Only results mentioning these strings will be included.
        must_exclude : list of str
            Any result mentioning these strings will be excluded.
        autogenerate_expansions : bool
            Do you want to generate expansions automatically using a LLM?
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
            The results of the search.

        Raises
        ------
        TypeError
            If both question and search are specified
        TypeError
            If neither question nor search are specified
        RuntimeError
            If the response fails in any way.
        ValueError
            If `n_results` is greater than 100.

        Notes
        -----
        You must provide either a `question` string or a `Search` object, not both.
        The search parameters will be set from the provided object or string and any additional keyword arguments.
        include_companies and exclude_companies must be the Google KG IDs of public companies.

        Examples
        --------
        >>> from nosible.classes.search import Search
        >>> from nosible import Nosible
        >>> s = Search(question="Hedge funds seek to expand into private credit", n_results=10)
        >>> with Nosible() as nos:
        ...     results = nos.search(search=s)
        ...     print(isinstance(results, ResultSet))
        ...     print(len(results))
        True
        10
        >>> nos = Nosible(nosible_api_key="test|xyz")
        >>> nos.search()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError: Specify exactly one of 'question' or 'search'.
        >>> nos = Nosible(nosible_api_key="test|xyz")
        >>> nos.search(question="foo", search=s)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError: Specify exactly one of 'question' or 'search'.
        >>> nos = Nosible(nosible_api_key="test|xyz")
        >>> nos.search(question="foo", n_results=101)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: Search can not have more than 100 results - Use bulk search instead.
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
            min_similarity=min_similarity,
            must_include=must_include,
            must_exclude=must_exclude,
            autogenerate_expansions=autogenerate_expansions,
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

        future = self._executor.submit(self._search_single, search_obj)
        try:
            return future.result()
        except ValueError:
            # Propagate our own “too many results” error directly
            raise
        except Exception as e:
            self.logger.warning(f"Search for {search_obj.question!r} failed: {e}")
            raise RuntimeError(f"Search for {search_obj.question!r} failed") from e

    def searches(
        self,
        *,
        searches: Union[SearchSet, list[Search]] = None,
        questions: list[str] = None,
        expansions: list[str] = None,
        sql_filter: list[str] = None,
        n_results: int = 100,
        n_probes: int = 30,
        n_contextify: int = 128,
        algorithm: str = "hybrid-2",
        min_similarity: float = None,
        must_include: list[str] = None,
        must_exclude: list[str] = None,
        autogenerate_expansions: bool = False,
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
        searches: SearchSet or list of Search
            The searches execute.
        questions : list of str
            The search queries to execute.
        expansions : list of str, optional
            List of expansion terms to use for each search.
        sql_filter : list of str, optional
            SQL-like filters to apply to the search.
        n_results : int
            Number of results to return per search.
        n_probes : int
            Number of probes to use for the search algorithm.
        n_contextify : int
            Context window size for the search.
        algorithm : str
            Search algorithm to use.
        min_similarity : float
            Results must have at least this similarity score.
        must_include : list of str
            Only results mentioning these strings will be included.
        must_exclude : list of str
            Any result mentioning these strings will be excluded.
        autogenerate_expansions : bool
            Do you want to generate expansions automatically using a LLM?.
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
        ...     [
        ...         Search(question="Hedge funds seek to expand into private credit", n_results=5),
        ...         Search(question="How have the Trump tariffs impacted the US economy?", n_results=5),
        ...     ]
        ... )
        >>> with Nosible() as nos:
        ...     results_list = list(nos.searches(searches=queries))
        >>> print(len(results_list))
        2
        >>> for r in results_list:
        ...     print(isinstance(r, ResultSet), bool(r))
        True True
        True True
        >>> with Nosible() as nos:
        ...     results_list_str = list(
        ...         nos.searches(
        ...             questions=[
        ...                 "What are the terms of the partnership between Microsoft and OpenAI?",
        ...                 "What are the terms of the partnership between Volkswagen and Uber?",
        ...             ]
        ...         )
        ...     )
        >>> nos = Nosible(nosible_api_key="test|xyz")  # doctest: +ELLIPSIS
        >>> nos.searches()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError: Specify exactly one of 'questions' or 'searches'.
        >>> from nosible import Nosible
        >>> nos = Nosible(nosible_api_key="test|xyz")
        >>> nos.searches(questions=["A"], searches=SearchSet(searches=["A"]))  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError: Specify exactly one of 'questions' or 'searches'.
        """
        if (questions is None and searches is None) or (questions is not None and searches is not None):
            raise TypeError("Specify exactly one of 'questions' or 'searches'.")

        # Function to ensure correct errors are raised.
        def _run_generator():
            search_queries = questions if questions is not None else searches

            searches_list = self._construct_search(
                question=search_queries,
                expansions=expansions,
                sql_filter=sql_filter,
                n_results=n_results,
                n_probes=n_probes,
                n_contextify=n_contextify,
                algorithm=algorithm,
                min_similarity=min_similarity,
                must_include=must_include,
                must_exclude=must_exclude,
                autogenerate_expansions=autogenerate_expansions,
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

            futures = [self._executor.submit(self._search_single, s) for s in searches_list]

            for future in futures:
                try:
                    yield future.result()
                except Exception as e:
                    self.logger.warning(f"Search failed: {e!r}")
                    raise

        return _run_generator()

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
        ValueError
            If min_similarity is not [0,1].

        Examples
        --------
        >>> from nosible.classes.search import Search
        >>> from nosible import Nosible
        >>> s = Search(question="Nvidia insiders dump more than $1 billion in stock", n_results=200)
        >>> with Nosible() as nos:
        ...     results = nos.search(search=s)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: Search can not have more than 100 results - Use bulk search instead.
        """
        # --------------------------------------------------------------------------------------------------------------
        # Setting search params. Individual search will override Nosible defaults.
        # --------------------------------------------------------------------------------------------------------------
        question = search_obj.question  # No default
        expansions = search_obj.expansions if search_obj.expansions is not None else []  # Default to empty list
        sql_filter = search_obj.sql_filter if search_obj.sql_filter is not None else None
        n_results = search_obj.n_results if search_obj.n_results is not None else 100
        n_probes = search_obj.n_probes if search_obj.n_probes is not None else 30
        n_contextify = search_obj.n_contextify if search_obj.n_contextify is not None else 128
        algorithm = search_obj.algorithm if search_obj.algorithm is not None else "hybrid-2"
        min_similarity = search_obj.min_similarity if search_obj.min_similarity is not None else 0
        must_include = search_obj.must_include if search_obj.must_include is not None else []
        must_exclude = search_obj.must_exclude if search_obj.must_exclude is not None else []
        autogenerate_expansions = (
            search_obj.autogenerate_expansions if search_obj.autogenerate_expansions is not None else False
        )
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

        if not (0.0 <= min_similarity <= 1.0):
            raise ValueError(f"Invalid min_simalarity: {min_similarity}.  Must be [0,1].")

        # Generate expansions if not provided
        if expansions is None:
            expansions = []
        if autogenerate_expansions is True:
            expansions = self._generate_expansions(question=question)

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
            "min_similarity": min_similarity,
            "must_include": must_include,
            "must_exclude": must_exclude,
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
        n_results: int = 1000,
        n_probes: int = 30,
        n_contextify: int = 128,
        algorithm: str = "hybrid-2",
        min_similarity: float = None,
        must_include: list[str] = None,
        must_exclude: list[str] = None,
        autogenerate_expansions: bool = False,
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
        verbose: bool = False,
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
        n_results : int
            Number of results per query (1,000–10,000).
        n_probes : int
            Number of shards to probe.
        n_contextify : int
            Context window size per result.
        algorithm : str
            Search algorithm identifier.
        min_similarity : float
            Results must have at least this similarity score.
        must_include : list of str
            Only results mentioning these strings will be included.
        must_exclude : list of str
            Any result mentioning these strings will be excluded.
        autogenerate_expansions : bool
            Do you want to generate expansions automatically using a LLM?
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
        verbose : bool, optional
            Show verbose output, Bulk search will print more information.

        Returns
        -------
        ResultSet
            The results of the bulk search.

        Raises
        ------
        ValueError
            If `n_results` is out of bounds (<1000 or >10000).
        TypeError
            If both question and search are specified.
        TypeError
            If neither question nor search are specified.
        RuntimeError
            If the response fails in any way.
        ValueError
            If min_similarity is not [0,1].

        Notes
        -----
        You must provide either a `question` string or a `Search` object, not both.
        The search parameters will be set from the provided object or string and any additional keyword arguments.

        Examples
        --------
        >>> from nosible.classes.search import Search  # doctest: +SKIP
        >>> from nosible import Nosible  # doctest: +SKIP
        >>> with Nosible(exclude_netlocs=["bbc.com"]) as nos:  # doctest: +SKIP
        ...     results = nos.bulk_search(question=_get_question(), n_results=2000)  # doctest: +SKIP
        ...     print(isinstance(results, ResultSet))  # doctest: +SKIP
        ...     print(len(results))  # doctest: +SKIP
        True
        2000
        >>> s = Search(question=_get_question(), n_results=1000)  # doctest: +SKIP
        >>> with Nosible() as nos:  # doctest: +SKIP
        ...     results = nos.bulk_search(search=s)  # doctest: +SKIP
        ...     print(isinstance(results, ResultSet))  # doctest: +SKIP
        ...     print(len(results))  # doctest: +SKIP
        True
        1000
        >>> nos = Nosible(nosible_api_key="test|xyz")  # doctest: +SKIP
        >>> nos.bulk_search()  # doctest: +SKIP
        Traceback (most recent call last):
        ...
        TypeError: Either question or search must be specified

        >>> nos = Nosible(nosible_api_key="test|xyz")  # doctest: +SKIP
        >>> nos.bulk_search(question=_get_question(), search=Search(question=_get_question()))  # doctest: +SKIP
        Traceback (most recent call last):
        ...
        TypeError: Question and search cannot be both specified
        >>> nos = Nosible(nosible_api_key="test|xyz")  # doctest: +SKIP
        >>> nos.bulk_search(question=_get_question(), n_results=100)  # doctest: +SKIP
        Traceback (most recent call last):
        ...
        ValueError: Bulk search must have at least 1000 results per query; use search() for smaller result sets.
        >>> nos = Nosible(nosible_api_key="test|xyz")  # doctest: +SKIP
        >>> nos.bulk_search(question=_get_question(), n_results=10001)  # doctest: +SKIP
        Traceback (most recent call last):  # doctest: +SKIP
        ...
        ValueError: Bulk search cannot have more than 10000 results per query.
        """
        from cryptography.fernet import Fernet

        previous_level = self.logger.level
        if verbose:
            self.logger.setLevel(logging.INFO)

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
            min_similarity = search.min_similarity if search.min_similarity is not None else min_similarity
            min_similarity = min_similarity if min_similarity is not None else 0
            must_include = search.must_include if search.must_include is not None else must_include
            must_include = must_include if must_include is not None else []
            must_exclude = search.must_exclude if search.must_exclude is not None else must_exclude
            must_exclude = must_exclude if must_exclude is not None else []
            autogenerate_expansions = (
                search.autogenerate_expansions
                if search.autogenerate_expansions is not None
                else autogenerate_expansions
            )
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
            expansions = []
        if autogenerate_expansions is True:
            expansions = self._generate_expansions(question=question)

        must_include = must_include if must_include is not None else []
        must_exclude = must_exclude if must_exclude is not None else []
        min_similarity = min_similarity if min_similarity is not None else 0

        if not (0.0 <= min_similarity <= 1.0):
            raise ValueError(f"Invalid min_simalarity: {min_similarity}.  Must be [0,1].")

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
        if n_results < 1000:
            raise ValueError(
                "Bulk search must have at least 1000 results per query; use search() for smaller result sets."
            )
        if n_results > 10000:
            raise ValueError("Bulk search cannot have more than 10000 results per query.")

        # Enforce Minimums
        filter_responses = n_results
        # Slow search must ask for at least 1 000
        n_results = max(n_results, 1000)

        self.logger.info(f"Performing bulk search for {question!r}...")

        try:
            payload = {
                "question": question,
                "expansions": expansions,
                "sql_filter": sql_filter,
                "n_results": n_results,
                "n_probes": n_probes,
                "n_contextify": n_contextify,
                "algorithm": algorithm,
                "min_similarity": min_similarity,
                "must_include": must_include,
                "must_exclude": must_exclude,
            }
            resp = self._post(url="https://www.nosible.ai/search/v1/slow-search", payload=payload)
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise ValueError(f"[{question!r}] HTTP {resp.status_code}: {resp.text}") from e

            data = resp.json()

            # Slow search: download & decrypt
            download_from = data.get("download_from")
            if ".zstd." in download_from:
                download_from = download_from.replace(".zstd.", ".gzip.", 1)
            decrypt_using = data.get("decrypt_using")
            for _ in range(100):
                dl = self._session.get(download_from, timeout=self.timeout)
                if dl.status_code == 200:
                    fernet = Fernet(decrypt_using.encode())
                    decrypted = fernet.decrypt(dl.content)
                    decompressed = gzip.decompress(decrypted)
                    api_resp = json_loads(decompressed)
                    return ResultSet.from_dicts(api_resp.get("response", [])[:filter_responses])
                time.sleep(10)
            raise ValueError("Results were not retrieved from Nosible")
        except Exception as e:
            self.logger.warning(f"Bulk search for {question!r} failed: {e}")
            raise RuntimeError(f"Bulk search for {question!r} failed") from e
        finally:
            # Restore whatever logging level we had before
            if verbose:
                self.logger.setLevel(previous_level)

    def answer(
        self,
        query: str,
        n_results: int = 100,
        min_similarity: float = 0.65,
        model: Union[str, None] = "google/gemini-2.0-flash-001",
        show_context: bool = True,
    ) -> str:
        """
        RAG-style question answering: retrieve top `n_results` via `.search()`
        then answer `query` using those documents as context.

        Parameters
        ----------
        query : str
            The user’s natural-language question.
        n_results : int
            How many docs to fetch to build the context.
        min_similarity : float
            Results must have at least this similarity score.
        model : str, optional
            Which LLM to call to answer your question.
        show_context : bool, optional
            Do you want the context to be shown?

        Returns
        -------
        str
            The LLM’s generated answer, grounded in the retrieved docs.

        Raises
        ------
        ValueError
            If no API key is configured for the LLM client.
        RuntimeError
            If the LLM call fails or returns an invalid response.

        Examples
        --------
        >>> from nosible import Nosible
        >>> with Nosible() as nos:
        ...     ans = nos.answer(
        ...         query="How is research governance and decision-making structured between Google and DeepMind?",
        ...         n_results=100,
        ...         show_context=True,
        ...     )  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        <BLANKLINE>
        Doc 1
        Title: ...
        >>> print(ans)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Answer:
        ...
        """

        if not self.llm_api_key:
            raise ValueError("An LLM API key is required for answer().")

        # Retrieve top documents
        results = self.search(question=query, n_results=n_results, min_similarity=min_similarity)

        # Build RAG context
        context = ""
        pieces: list[str] = []
        for idx, result in enumerate(results):
            pieces.append(f"""
                Doc {idx + 1}
                Title: {result.title}
                Similarity Score: {result.similarity * 100:.2f}%
                URL: {result.url}
                Content: {result.content}
                """)
            context = "\n".join(pieces)

        if show_context:
            print(textwrap.dedent(context))

        # Craft prompt
        prompt = f"""
            # TASK DESCRIPTION

            You are a helpful assistant.  Use the following context to answer the question.
            When you use information from a chunk, cite it by referencing its label in square brackets, e.g. [doc3].
            
            ## Question
            {query}
            
            ## Context
            {context}
            """
        from openai import OpenAI

        # Call LLM
        client = OpenAI(base_url=self.openai_base_url, api_key=self.llm_api_key)
        try:
            response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
        except Exception as e:
            raise RuntimeError(f"LLM API error: {e}") from e

        # Validate response shape
        choices = getattr(response, "choices", None)
        if not choices or not hasattr(choices[0], "message"):
            raise RuntimeError(f"Invalid LLM response format: {response!r}")

        # Return the generated text
        return "Answer:\n" + response.choices[0].message.content.strip()

    @_rate_limited("visit")
    def visit(self, html: str = "", recrawl: bool = False, render: bool = False, url: str = None) -> WebPageData:
        """
        Visit a given URL and return a structured WebPageData object for the page.

        Parameters
        ----------
        html : str
            Raw HTML to process instead of fetching.
        recrawl : bool
            If True, force a fresh crawl.
        render : bool
            If True, allow JavaScript rendering before extraction.
        url : str
            The URL to fetch and parse.

        Returns
        -------
        WebPageData
            Structured page data object.

        Raises
        ------
        TypeError
            If URL is not provided.
        ValueError
            If invalid JSON response from the server.
        ValueError
            If URL is not found.
        ValueError
            If the server did not send back a 'response' key.

        Examples
        --------
        >>> from nosible import Nosible
        >>> with Nosible() as nos:
        ...     out = nos.visit(url="https://www.dailynewsegypt.com/2023/09/08/g20-and-its-summits/")
        ...     print(isinstance(out, WebPageData))
        ...     print(hasattr(out, "languages"))
        ...     print(hasattr(out, "page"))
        True
        True
        True
        >>> with Nosible() as nos:
        ...     out = nos.visit()
        ...     print(isinstance(out, type(WebPageData)))
        ...     print(hasattr(out, "languages"))
        ...     print(hasattr(out, "page"))  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError: URL must be provided
        """
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

        if data == {"message": "Sorry, the URL could not be fetched."}:
            raise ValueError("The URL could not be found.")

        if "response" not in data:
            self.logger.error(f"No 'response' key in server response: {data}")
            raise ValueError("No 'response' key in server response")

        response_data = data["response"]
        return WebPageData(
            companies=response_data.get("companies"),
            full_text=response_data.get("full_text"),
            languages=response_data.get("languages"),
            metadata=response_data.get("metadata"),
            page=response_data.get("page"),
            request=response_data.get("request"),
            snippets=SnippetSet.from_dict(response_data.get("snippets", {})),
            statistics=response_data.get("statistics"),
            structured=response_data.get("structured"),
            url_tree=response_data.get("url_tree"),
        )

    @_rate_limited("fast")
    def trend(
        self,
        query: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sql_filter: Optional[str] = None,
    ) -> dict:
        """
        Extract a trend showing the volume of news surrounding your query.

        Parameters
        ----------
        query : str
            The search term we would like to see a trend for.
        start_date : str, optional
            ISO‐format start date (YYYY-MM-DD) of the trend window.
        end_date : str, optional
            ISO‐format end date (YYYY-MM-DD) of the trend window.
        sql_filter : str, optional
            An optional SQL filter to narrow down the trend query

        Returns
        -------
        dict
            The JSON-decoded trend data returned by the server.

        Examples
        --------
        >>> from nosible import Nosible
        >>> with Nosible() as nos:
        ...     trends_data = nos.trend("Christmas Shopping", start_date="2005-01-01", end_date="2020-12-31")
        ...     print(trends_data)  # doctest: +ELLIPSIS
        {'2005-01-31': ...'2020-12-31': ...}
        """
        # Validate dates
        if start_date is not None:
            self._validate_date_format(start_date, "start_date")
        if end_date is not None:
            self._validate_date_format(end_date, "end_date")

        payload: dict[str, str] = {"query": query}

        if sql_filter is not None:
            payload["sql_filter"] = sql_filter
        else:
            payload["sql_filter"] = "SELECT loc, published FROM engine"

        # Send the POST to the /trend endpoint
        response = self._post(url="https://www.nosible.ai/search/v1/trend", payload=payload)
        # Will raise ValueError on rate-limit or auth errors
        response.raise_for_status()
        payload = response.json().get("response", {})

        # if no window requested, return everything
        if start_date is None and end_date is None:
            return payload

        # Filter by ISO‐date keys
        filtered: dict[str, float] = {}
        for date_str, value in payload.items():
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue
            filtered[date_str] = value

        return filtered

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

        Examples
        --------
        >>> from nosible import Nosible
        >>> with Nosible() as nos:
        ...     print(nos.indexed(url="https://www.dailynewsegypt.com/2023/09/08/g20-and-its-summits/"))
        True
        """
        response = self._post(url="https://www.nosible.ai/search/v1/indexed", payload={"url": url})

        try:
            response.raise_for_status()
            data = response.json()
            msg = data.get("message")
            if msg == "The URL is in the system.":
                return True
            if msg == "The URL is nowhere to be found.":
                return False
            if msg == "The URL could not be retrieved.":
                return False
            # If we reach here, the response is unexpected
            return False
        except httpx.HTTPError:
            return False
        except:
            return False

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
        >>> nos = Nosible(nosible_api_key="test|xyz")
        >>> print(nos.get_rate_limits())  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Below are the rate limits for all NOSIBLE plans.
        To upgrade your package, visit https://www.nosible.ai/products.
        <BLANKLINE>
        Unless otherwise indicated, bulk searches are limited to one-at-a-time per API key.
        <BLANKLINE>
        Free: (Your current plan)
        | Endpoint    | Per Month | Per Minute | Effective CPM |
        | ----------- | --------- | ---------- | ------------- |
        | Search      |      3000 |         60 |         $4.00 |
        | URL Visits  |       300 |         60 |         $4.00 |
        | Bulk Search |       300 |         60 |         $4.00 |
        <BLANKLINE>
        Basic ($49p/m):
        | Endpoint    | Per Month | Per Minute | Effective CPM |
        ...
        """
        # Human-friendly plan names
        display = {
            "test": "Free",
            "basic": "Basic ($49p/m)",
            "pro": "Pro ($199p/m)",
            "pro+": "Pro+ ($799p/m)",
            "bus": "Business ($3999p/m)",
            "bus+": "Business+ ($7499p/m)",
            "ent": "Enterprise ($14999p/m)",
        }

        # Human-friendly endpoint names
        endpoint_name = {"fast": "Search", "visit": "URL Visits", "slow": "Bulk Search"}

        out = [
            "Below are the rate limits for all NOSIBLE plans.",
            "To upgrade your package, visit https://www.nosible.ai/products.\n",
            "Unless otherwise indicated, bulk searches are limited to one-at-a-time per API key.\n",
        ]

        user_plan = self._get_user_plan()
        current_plan = ""
        cpm_counter = 4.0

        # Preserve the order you care about:
        for plan in ["test", "basic", "pro", "pro+", "bus", "bus+", "ent"]:
            name = display.get(plan, plan)
            if plan == user_plan:
                current_plan = " (Your current plan)"

            out.append(f"{name}:{current_plan}")
            out.append("| Endpoint    | Per Month | Per Minute | Effective CPM |")
            out.append("| ----------- | --------- | ---------- | ------------- |")

            for ep in ["fast", "visit", "slow"]:
                buckets = PLAN_RATE_LIMITS[plan][ep]
                # Find minute & day
                minute = next(limit for limit, i in buckets if i == 60)
                month = next(limit for limit, i in buckets if i == 24 * 3600 * 30)
                cpm = f"${cpm_counter:.2f}"

                out.append(f"| {endpoint_name[ep]:<11} | {month:>9} | {minute:>10} | {cpm:>13} |")

            cpm_counter = cpm_counter - 0.5
            out.append("")  # Blank line
            current_plan = ""

        return "\n".join(out)

    def close(self):
        """
        Close the Nosible client, shutting down the HTTP session
        and thread pool to release network and threading resources.

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

    def _post(self, url: str, payload: dict, headers: dict = None, timeout: int = None) -> httpx.Response:
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

        Raises
        ------
        ValueError
            If the user API key is invalid.
        ValueError
            If the user hits their rate limit.
        ValueError
            If the user is making too many concurrent searches.
        ValueError
            If an unexpected error occurs.
        ValueError
            If NOSIBLE is currently restarting.
        ValueError
            If NOSIBLE is currently overloaded.

        Returns
        -------
        httpx.Response
            The HTTP response object.
        """
        response = self._session.post(
            url=url,
            json=payload,
            headers=headers if headers is not None else self.headers,
            timeout=timeout if timeout is not None else self.timeout,
            follow_redirects=True,
        )

        # If unauthorized, or if the payload is string too short, treat as invalid API key
        if response.status_code == 401:
            raise ValueError("Your API key is not valid.")
        if response.status_code == 422:
            content_type = response.headers.get("Content-Type", "")
            if content_type.startswith("application/json"):
                body = response.json()
                if isinstance(body, list):
                    body = body[0]
                print(body)
                if body.get("type") == "string_too_short":
                    raise ValueError("Your API key is not valid: Too Short.")
            else:
                raise ValueError("You made a bad request.")
        if response.status_code == 429:
            raise ValueError("You have hit your rate limit.")
        if response.status_code == 409:
            raise ValueError("Too many concurrent searches.")
        if response.status_code == 500:
            raise ValueError("An unexpected error occurred.")
        if response.status_code == 502:
            raise ValueError("NOSIBLE is currently restarting.")
        if response.status_code == 504:
            raise ValueError("NOSIBLE is currently overloaded.")

        return response

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

        Examples
        --------
        >>> nos = Nosible(nosible_api_key="test+|xyz")  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
        ...
        ValueError: Your API key is not valid: test+ is not a valid plan prefix.
        """
        # Split off anything after the first '|'
        prefix = (self.nosible_api_key or "").split("|", 1)[0]

        # Map prefixes -> plan names
        plans = {"test", "basic", "pro", "pro+", "bus", "bus+", "ent", "chat"}

        if prefix not in plans:
            raise ValueError(f"Your API key is not valid: {prefix} is not a valid plan prefix.")

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

        Examples
        --------
        >>> from nosible import Nosible
        >>> nos = Nosible(llm_api_key=None)
        >>> nos.llm_api_key = None
        >>> nos._generate_expansions("anything")  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
        ...
        ValueError: LLM API key is required for generating expansions.
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
        # Lazy load
        from openai import OpenAI

        client = OpenAI(base_url=self.openai_base_url, api_key=self.llm_api_key)

        # Call the chat completions endpoint.
        resp = client.chat.completions.create(
            model=self.expansions_model, messages=[{"role": "user", "content": prompt.strip()}], temperature=0.7
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

    @staticmethod
    def _validate_date_format(string: str, name: str):
        """
        Check that a date string is valid ISO format (YYYY-MM-DD or full ISO timestamp).

        Parameters
        ----------
        string : str
            The date string to validate.
        name : str
            The name of the parameter being validated, used in the error message.

        Raises
        ------
        ValueError
            If `string` is not a valid ISO 8601 date. Error message will include
            the `name` and the offending string.
                Examples
        --------
        >>> # valid date-only format
        >>> Nosible._validate_date_format("2023-12-31", "publish_start")
        >>> # valid full timestamp
        >>> Nosible._validate_date_format("2023-12-31T15:30:00", "visited_end")
        >>> # invalid month
        >>> Nosible._validate_date_format("2023-13-01", "publish_end")
        Traceback (most recent call last):
            ...
        ValueError: Invalid date for 'publish_end': '2023-13-01'.  Expected ISO format 'YYYY-MM-DD'.
        >>> # wrong separator
        >>> Nosible._validate_date_format("2023/12/31", "visited_start")
        Traceback (most recent call last):
            ...
        ValueError: Invalid date for 'visited_start': '2023/12/31'.  Expected ISO format 'YYYY-MM-DD'.
        """
        dateregex = r"^\d{4}-\d{2}-\d{2}"

        if not re.match(dateregex, string):
            raise ValueError(f"Invalid date for '{name}': {string!r}.  Expected ISO format 'YYYY-MM-DD'.")

        try:
            # datetime.fromisoformat accepts both YYYY-MM-DD and full timestamps
            parsed = datetime.fromisoformat(string)
        except Exception:
            raise ValueError(f"Invalid date for '{name}': {string!r}.  Expected ISO format 'YYYY-MM-DD'.")

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
        str
            An SQL query string with appropriate WHERE clauses.

        Raises
        ------
        ValueError
            If more than 50 items in a filter are given.
        """
        for name, value in [
            ("publish_start", publish_start),
            ("publish_end", publish_end),
            ("visited_start", visited_start),
            ("visited_end", visited_end),
        ]:
            if value is not None:
                self._validate_date_format(string=value, name=name)

        # Validate list lengths
        for name, value in [
            ("include_netlocs", include_netlocs),
            ("exclude_netlocs", exclude_netlocs),
            ("include_languages", include_languages),
            ("exclude_languages", exclude_languages),
            ("include_companies", include_companies),
            ("exclude_companies", exclude_companies),
            ("include_docs", include_docs),
            ("exclude_docs", exclude_docs),
        ]:
            if value is not None and len(value) > 50:
                raise ValueError(f"Too many items for '{name}' filter ({len(value)}); maximum allowed is 50.")

        sql = ["SELECT loc FROM engine"]
        clauses: list[str] = []

        # Published date range
        if publish_start or publish_end:
            if publish_start and publish_end:
                clauses.append(f"published >= '{publish_start}' AND published <= '{publish_end}'")
            elif publish_start:
                clauses.append(f"published >= '{publish_start}'")
            else:  # Only publish_end
                clauses.append(f"published <= '{publish_end}'")

        # Visited date range
        if visited_start or visited_end:
            if visited_start and visited_end:
                clauses.append(f"visited >= '{visited_start}' AND visited <= '{visited_end}'")
            elif visited_start:
                clauses.append(f"visited >= '{visited_start}'")
            else:  # Only visited_end
                clauses.append(f"visited <= '{visited_end}'")

        # date certainty filter
        if certain is True:
            clauses.append("certain = TRUE")
        elif certain is False:
            clauses.append("certain = FALSE")

        # Include netlocs with both www/non-www variants
        if include_netlocs:
            variants = set()
            for n in include_netlocs:
                variants.add(n)
                if n.startswith("www."):
                    variants.add(n[4:])
                else:
                    variants.add("www." + n)
            in_list = ", ".join(f"'{v}'" for v in sorted(variants))
            clauses.append(f"netloc IN ({in_list})")

        # Exclude netlocs with both www/non-www variants
        if exclude_netlocs:
            variants = set()
            for n in exclude_netlocs:
                variants.add(n)
                if n.startswith("www."):
                    variants.add(n[4:])
                else:
                    variants.add("www." + n)
            ex_list = ", ".join(f"'{v}'" for v in sorted(variants))
            clauses.append(f"netloc NOT IN ({ex_list})")

        # Include / exclude companies
        if include_companies:
            company_list = ", ".join(f"'{c}'" for c in include_companies)
            clauses.append(
                f"(company_1 IN ({company_list}) OR company_2 IN ({company_list}) OR company_3 IN ({company_list}))"
            )
        if exclude_companies:
            company_list = ", ".join(f"'{c}'" for c in exclude_companies)
            clauses.append(
                f"(company_1 NOT IN ({company_list}) AND company_2 NOT IN ({company_list}) AND company_3 NOT IN ({company_list}))"
            )

        # Include / exclude languages
        if include_languages:
            langs = ", ".join(f"'{lang}-{lang}'" for lang in include_languages)
            clauses.append(f"language IN ({langs})")
        if exclude_languages:
            langs = ", ".join(f"'{lang}-{lang}'" for lang in exclude_languages)
            clauses.append(f"language NOT IN ({langs})")

        if include_docs:
            # Assume these are URL hashes, e.g. "ENNmqkF1mGNhVhvhmbUEs4U2"
            doc_hashes = ", ".join(f"'{doc}'" for doc in include_docs)
            clauses.append(f"doc_hash IN ({doc_hashes})")

        if exclude_docs:
            # Assume these are URL hashes, e.g. "ENNmqkF1mGNhVhvhmbUEs4U2"
            doc_hashes = ", ".join(f"'{doc}'" for doc in exclude_docs)
            clauses.append(f"doc_hash NOT IN ({doc_hashes})")

        # Join everything
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
        import polars as pl  # Lazy import

        # Create a dummy DataFrame with correct columns and no rows
        df = pl.DataFrame({col: [] for col in columns})
        ctx = pl.SQLContext()
        ctx.register("engine", df)
        try:
            ctx.execute(sql)
            return True
        except Exception:
            return False

    def __enter__(self) -> "Nosible":
        """
        Enter the context manager, returning this client instance.

        Returns
        -------
        Nosible
            The current client instance.
        """
        return self

    def __exit__(
        self,
        _exc_type: Optional[type[BaseException]],
        _exc_val: Optional[BaseException],
        _exc_tb: Optional[types.TracebackType],
    ) -> Optional[bool]:
        """
        Always clean up (self.close()), but let exceptions propagate.
        Return True only if you really want to suppress an exception.

        Parameters
        ----------
        _exc_type : Optional[type[BaseException]]
            The type of the exception raised, if any.
        _exc_val : Optional[BaseException]
            The exception instance, if any.
        _exc_tb : Optional[types.TracebackType]
            The traceback object, if any.

        Returns
        -------
        Optional[bool]
            False to propagate exceptions, True to suppress them.
        """
        try:
            self.close()
        except Exception as cleanup_err:
            # optional: log or re-raise, but don’t hide the original exc
            print(f"Cleanup failed: {cleanup_err!r}")
        # Return False (or None) => exceptions inside the with‐block are re-raised.
        return False

    def __del__(self):
        """
        Destructor to ensure resources are cleaned up if not explicitly closed.

        """
        # Only close if interpreter is fully alive
        if not getattr(sys, "is_finalizing", lambda: False)():
            try:
                self.close()
            except Exception:
                pass
