"""Synchronous client for the merged NOSIBLE Search and World APIs."""

import os
import gzip
import json
import logging
import math
import re
import textwrap
import time
import types
import warnings
from calendar import monthrange
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from functools import partial
from typing import Any, Dict, FrozenSet, List, Optional, Tuple, Union
from urllib.parse import urlsplit

import httpx
import polars as pl
import zstandard
from cryptography.fernet import Fernet, InvalidToken
from openai import OpenAI, OpenAIError

from nosible.classes.result_set import ResultSet
from nosible.classes.rich_result import RichResult
from nosible.classes.search import Search
from nosible.classes.search_set import SearchSet
from nosible.classes.snippet_set import SnippetSet
from nosible.classes.web_page import WebPageData
from nosible.exceptions import error_from_response
from nosible.transport import NosibleTransport
from nosible.world_client import WorldClient

LOGGER = logging.getLogger(name=__name__)
SEARCH_ALGORITHMS: FrozenSet[str] = frozenset(
    {
        "string",
        "lexical",
        "baseline",
        "hamming",
        "hybrid-1",
        "hybrid-2",
        "hybrid-3",
        "company"
    }
)
SEARCH_BRAND_SAFETY: FrozenSet[str] = frozenset(
    {
        "Safe",
        "Sensitive",
        "Unsafe"
    }
)
SEARCH_CONTINENTS: FrozenSet[str] = frozenset(
    {
        "Africa",
        "Asia",
        "Europe",
        "North America",
        "Oceania",
        "South America",
        "Worldwide"
    }
)
SEARCH_LANGUAGES: FrozenSet[str] = frozenset(
    """
    af am ar as az be bg bn br bs ca cs cy da de el en eo es et eu fa fi fr fy
    ga gd gl gu ha he hi hr hu hy id is it ja jv ka kk km kn ko ku ky la lo lt
    lv mg mk ml mn mr ms my ne nl no om or pa pl ps pt ro ru sa sd sh si sk sl
    so sq sr su sv sw ta te th tl tr ug uk ur uz vi xh yi zh
    """.split()
)


class Nosible:
    """High-level synchronous client for NOSIBLE Search and World."""

    def __init__(
        self: "Nosible",
        nosible_api_key: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        openai_base_url: str = "https://openrouter.ai/api/v1",
        sentiment_model: str = "openai/gpt-4o",
        expansions_model: str = "openai/gpt-4o",
        timeout: int = 30,
        retries: int = 5,
        concurrency: int = 10,
        publish_start: Optional[str] = None,
        publish_end: Optional[str] = None,
        include_netlocs: Optional[List[str]] = None,
        exclude_netlocs: Optional[List[str]] = None,
        visited_start: Optional[str] = None,
        visited_end: Optional[str] = None,
        certain: Optional[bool] = None,
        include_companies: Optional[List[str]] = None,
        exclude_companies: Optional[List[str]] = None,
        include_docs: Optional[List[str]] = None,
        exclude_docs: Optional[List[str]] = None,
        brand_safety: Optional[str] = None,
        language: Optional[str] = None,
        continent: Optional[str] = None,
        region: Optional[str] = None,
        country: Optional[str] = None,
        sector: Optional[str] = None,
        industry_group: Optional[str] = None,
        industry: Optional[str] = None,
        sub_industry: Optional[str] = None,
        iab_tier_1: Optional[str] = None,
        iab_tier_2: Optional[str] = None,
        iab_tier_3: Optional[str] = None,
        iab_tier_4: Optional[str] = None,
        instruction: Optional[str] = None,
        base_url: str = "https://nosible.world/api",
        http_client: Optional[httpx.Client] = None,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Initialise a shared Search and World client.

        :param nosible_api_key: NOSIBLE API key or None to use NOSIBLE_API_KEY.
        :param llm_api_key: LLM API key or None to use LLM_API_KEY.
        :param openai_base_url: OpenAI-compatible LLM base URL.
        :param sentiment_model: Model used for sentiment scoring.
        :param expansions_model: Model used for query expansions.
        :param timeout: Default HTTP timeout in seconds.
        :param retries: Maximum transport attempts.
        :param concurrency: Retained batch-convenience concurrency setting.
        :param publish_start: Default earliest publication date.
        :param publish_end: Default latest publication date.
        :param include_netlocs: Default domains to include.
        :param exclude_netlocs: Default domains to exclude.
        :param visited_start: Default earliest visit date.
        :param visited_end: Default latest visit date.
        :param certain: Default date-certainty filter.
        :param include_companies: Default company identifiers to include.
        :param exclude_companies: Default company identifiers to exclude.
        :param include_docs: Default document hashes to include.
        :param exclude_docs: Default document hashes to exclude.
        :param brand_safety: Default brand-safety filter.
        :param language: Default ISO language filter.
        :param continent: Default continent filter.
        :param region: Default region filter.
        :param country: Default country filter.
        :param sector: Default GICS sector filter.
        :param industry_group: Default GICS industry-group filter.
        :param industry: Default GICS industry filter.
        :param sub_industry: Default GICS sub-industry filter.
        :param iab_tier_1: Default IAB tier-one filter.
        :param iab_tier_2: Default IAB tier-two filter.
        :param iab_tier_3: Default IAB tier-three filter.
        :param iab_tier_4: Default IAB tier-four filter.
        :param instruction: Default retrieval instruction.
        :param base_url: Merged NOSIBLE API base URL.
        :param http_client: Optional caller-owned HTTPX client.
        :param args: Ignored legacy positional arguments.
        :param kwargs: Deprecated legacy keyword arguments.
        :return: None.
        """
        if args:
            warnings.warn(
                message="Additional positional arguments are ignored",
                category=DeprecationWarning,
                stacklevel=2
            )
        if "include_languages" in kwargs or "exclude_languages" in kwargs:
            warnings.warn(
                message="Language list filters are deprecated; use 'language'",
                category=DeprecationWarning,
                stacklevel=2
            )
        if isinstance(timeout, bool) or timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        if isinstance(concurrency, bool) or concurrency <= 0:
            raise ValueError("concurrency must be greater than zero")

        self.nosible_api_key = nosible_api_key or os.getenv(key="NOSIBLE_API_KEY")
        self.llm_api_key = llm_api_key or os.getenv(key="LLM_API_KEY")
        self.openai_base_url = openai_base_url
        self.sentiment_model = sentiment_model
        self.expansions_model = expansions_model
        self.timeout = timeout
        self.retries = retries
        self.concurrency = concurrency
        self.base_url = os.fspath(path=base_url).rstrip("/")
        self.owns_http_client = http_client is None
        self.session = http_client or httpx.Client(follow_redirects=True)
        self.transport = NosibleTransport(
            base_url=self.base_url,
            api_key=self.nosible_api_key,
            client=self.session,
            timeout=self.timeout,
            retries=self.retries
        )
        self.world = WorldClient(transport=self.transport)
        self.headers = {
            "Accept-Encoding": "gzip, zstd",
            "Content-Type": "application/json"
        }
        if self.nosible_api_key:
            self.headers["api-key"] = self.nosible_api_key
        self.closed = False
        self.publish_start = publish_start
        self.publish_end = publish_end
        self.include_netlocs = include_netlocs
        self.exclude_netlocs = exclude_netlocs
        self.visited_start = visited_start
        self.visited_end = visited_end
        self.certain = certain
        self.include_companies = include_companies
        self.exclude_companies = exclude_companies
        self.include_docs = include_docs
        self.exclude_docs = exclude_docs
        self.brand_safety = brand_safety
        self.language = language
        self.continent = continent
        self.region = region
        self.country = country
        self.sector = sector
        self.industry_group = industry_group
        self.industry = industry
        self.sub_industry = sub_industry
        self.iab_tier_1 = iab_tier_1
        self.iab_tier_2 = iab_tier_2
        self.iab_tier_3 = iab_tier_3
        self.iab_tier_4 = iab_tier_4
        self.instruction = instruction

    def __enter__(
        self: "Nosible"
    ) -> "Nosible":
        """
        Enter a client context.

        :return: This client.
        """
        return self

    def __exit__(
        self: "Nosible",
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[types.TracebackType]
    ) -> Optional[bool]:
        """
        Close the client and propagate context exceptions.

        :param exc_type: Exception type raised in the context.
        :param exc_value: Exception value raised in the context.
        :param traceback: Exception traceback raised in the context.
        :return: False so context exceptions propagate.
        """
        self.close()
        return False

    def search(
        self: "Nosible",
        prompt: Optional[str] = None,
        agent: str = "cybernaut-1"
    ) -> ResultSet:
        """
        Run agentic Search with Cybernaut.

        :param prompt: Agent instruction from 25 to 2,500 characters.
        :param agent: Agent identifier.
        :return: Agentic search results.
        """
        if not isinstance(prompt, str) or not 25 <= len(prompt) <= 2500:
            raise ValueError(
                "prompt must contain between 25 and 2500 characters"
            )
        if agent != "cybernaut-1":
            raise ValueError("agent must be 'cybernaut-1'")
        data = self.search_json(
            endpoint="search",
            payload={
                "prompt": prompt,
                "agent": agent
            }
        )
        return ResultSet.from_dict(data=data)

    def fast_searches(
        self: "Nosible",
        searches: Optional[Union[SearchSet, List[Search]]] = None,
        questions: Optional[List[str]] = None,
        expansions: Optional[List[str]] = None,
        sql_filter: Optional[str] = None,
        n_results: int = 100,
        n_probes: int = 30,
        n_contextify: int = 128,
        algorithm: str = "hybrid-3",
        min_similarity: Optional[float] = None,
        must_include: Optional[List[str]] = None,
        must_exclude: Optional[List[str]] = None,
        autogenerate_expansions: bool = False,
        publish_start: Optional[str] = None,
        publish_end: Optional[str] = None,
        include_netlocs: Optional[List[str]] = None,
        exclude_netlocs: Optional[List[str]] = None,
        visited_start: Optional[str] = None,
        visited_end: Optional[str] = None,
        certain: Optional[bool] = None,
        include_companies: Optional[List[str]] = None,
        exclude_companies: Optional[List[str]] = None,
        include_docs: Optional[List[str]] = None,
        exclude_docs: Optional[List[str]] = None,
        brand_safety: Optional[str] = None,
        language: Optional[str] = None,
        continent: Optional[str] = None,
        region: Optional[str] = None,
        country: Optional[str] = None,
        sector: Optional[str] = None,
        industry_group: Optional[str] = None,
        industry: Optional[str] = None,
        sub_industry: Optional[str] = None,
        iab_tier_1: Optional[str] = None,
        iab_tier_2: Optional[str] = None,
        iab_tier_3: Optional[str] = None,
        iab_tier_4: Optional[str] = None,
        instruction: Optional[str] = None,
        companies: Optional[List[str]] = None,
        collection: Optional[str] = None,
        deduplicate: Optional[bool] = None,
        internal_use: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Iterator[ResultSet]:
        """
        Run several Fast searches and return an iterator over results.

        :param searches: Search objects to execute.
        :param questions: Question strings to execute.
        :param expansions: Shared query expansions.
        :param sql_filter: Shared SQL filter.
        :param n_results: Results requested per search.
        :param n_probes: Search probes per request.
        :param n_contextify: Context size per result.
        :param algorithm: Retrieval algorithm.
        :param min_similarity: Minimum similarity score.
        :param must_include: Required strings.
        :param must_exclude: Forbidden strings.
        :param autogenerate_expansions: Whether to generate LLM expansions.
        :param publish_start: Earliest publication date.
        :param publish_end: Latest publication date.
        :param include_netlocs: Domains to include.
        :param exclude_netlocs: Domains to exclude.
        :param visited_start: Earliest visit date.
        :param visited_end: Latest visit date.
        :param certain: Whether dates must be certain.
        :param include_companies: Company identifiers to include.
        :param exclude_companies: Company identifiers to exclude.
        :param include_docs: Document hashes to include.
        :param exclude_docs: Document hashes to exclude.
        :param brand_safety: Brand-safety filter.
        :param language: ISO language filter.
        :param continent: Continent filter.
        :param region: Region filter.
        :param country: Country filter.
        :param sector: GICS sector filter.
        :param industry_group: GICS industry-group filter.
        :param industry: GICS industry filter.
        :param sub_industry: GICS sub-industry filter.
        :param iab_tier_1: IAB tier-one filter.
        :param iab_tier_2: IAB tier-two filter.
        :param iab_tier_3: IAB tier-three filter.
        :param iab_tier_4: IAB tier-four filter.
        :param instruction: Retrieval instruction.
        :param companies: Company names to refine retrieval.
        :param collection: Search collection.
        :param deduplicate: Whether to remove duplicate headlines.
        :param internal_use: Private feature controls.
        :param kwargs: Deprecated language-list filters.
        :return: Iterator over completed result sets.
        """
        if (searches is None) == (questions is None):
            raise TypeError(
                "Specify exactly one of 'questions' or 'searches'."
            )
        warn_legacy_language_filters(kwargs=kwargs)
        search_calls = []
        if questions is not None:
            if not isinstance(questions, list) or any(
                not isinstance(question, str)
                for question in questions
            ):
                raise TypeError("questions must be a list of strings")
            for question in questions:
                search_calls.append(
                    partial(
                        self.fast_search,
                        question=question,
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
                        include_companies=include_companies,
                        exclude_companies=exclude_companies,
                        include_docs=include_docs,
                        exclude_docs=exclude_docs,
                        brand_safety=brand_safety,
                        language=language,
                        continent=continent,
                        region=region,
                        country=country,
                        sector=sector,
                        industry_group=industry_group,
                        industry=industry,
                        sub_industry=sub_industry,
                        iab_tier_1=iab_tier_1,
                        iab_tier_2=iab_tier_2,
                        iab_tier_3=iab_tier_3,
                        iab_tier_4=iab_tier_4,
                        instruction=instruction,
                        companies=companies,
                        collection=collection,
                        deduplicate=deduplicate,
                        internal_use=internal_use
                    )
                )
        else:
            search_values = (
                searches.searches_list
                if isinstance(searches, SearchSet)
                else searches
            )
            if not isinstance(search_values, list) or any(
                not isinstance(search_value, Search)
                for search_value in search_values
            ):
                raise TypeError(
                    "searches must be a SearchSet or list of Search objects"
                )
            for search_value in search_values:
                search_calls.append(
                    partial(
                        self.fast_search,
                        search=search_value,
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
                        include_companies=include_companies,
                        exclude_companies=exclude_companies,
                        include_docs=include_docs,
                        exclude_docs=exclude_docs,
                        brand_safety=brand_safety,
                        language=language,
                        continent=continent,
                        region=region,
                        country=country,
                        sector=sector,
                        industry_group=industry_group,
                        industry=industry,
                        sub_industry=sub_industry,
                        iab_tier_1=iab_tier_1,
                        iab_tier_2=iab_tier_2,
                        iab_tier_3=iab_tier_3,
                        iab_tier_4=iab_tier_4,
                        instruction=instruction,
                        companies=companies,
                        collection=collection,
                        deduplicate=deduplicate,
                        internal_use=internal_use
                    )
                )
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = [
                executor.submit(search_call)
                for search_call in search_calls
            ]
            result_sets = [
                future.result()
                for future in futures
            ]
        return iter(result_sets)

    def rich_search(
        self: "Nosible",
        question: str,
        instruction: Optional[str] = None,
        expansions: Optional[List[str]] = None,
        sql_filter: Optional[str] = None,
        algorithm: str = "hybrid-3",
        min_similarity: Optional[float] = None,
        must_include: Optional[List[str]] = None,
        must_exclude: Optional[List[str]] = None,
        brand_safety: Optional[str] = None,
        language: Optional[str] = None,
        continent: Optional[str] = None,
        region: Optional[str] = None,
        country: Optional[str] = None,
        sector: Optional[str] = None,
        industry_group: Optional[str] = None,
        industry: Optional[str] = None,
        sub_industry: Optional[str] = None,
        iab_tier_1: Optional[str] = None,
        iab_tier_2: Optional[str] = None,
        iab_tier_3: Optional[str] = None,
        iab_tier_4: Optional[str] = None,
        companies: Optional[List[str]] = None,
        collection: Optional[str] = None,
        deduplicate: Optional[bool] = None,
        internal_use: Optional[Dict[str, Any]] = None,
        n_results: int = 10,
        n_probes: int = 30,
        n_contextify: int = 256,
        enrich_profile: bool = True,
        enrich_targeting: bool = True,
        enrich_history: bool = True,
        enrich_signals: bool = True,
        enrich_vectors: bool = True
    ) -> ResultSet:
        """
        Run Rich Search with optional enrichment blocks.

        :param question: Search question.
        :param instruction: Retrieval instruction.
        :param expansions: Query expansions.
        :param sql_filter: SQL filter.
        :param algorithm: Retrieval algorithm.
        :param min_similarity: Minimum similarity score.
        :param must_include: Required strings.
        :param must_exclude: Forbidden strings.
        :param brand_safety: Brand-safety filter.
        :param language: ISO language filter.
        :param continent: Continent filter.
        :param region: Region filter.
        :param country: Country filter.
        :param sector: GICS sector filter.
        :param industry_group: GICS industry-group filter.
        :param industry: GICS industry filter.
        :param sub_industry: GICS sub-industry filter.
        :param iab_tier_1: IAB tier-one filter.
        :param iab_tier_2: IAB tier-two filter.
        :param iab_tier_3: IAB tier-three filter.
        :param iab_tier_4: IAB tier-four filter.
        :param companies: Company names to refine retrieval.
        :param collection: Search collection.
        :param deduplicate: Whether to remove duplicate headlines.
        :param internal_use: Private feature controls.
        :param n_results: Requested result count.
        :param n_probes: Number of search probes.
        :param n_contextify: Context size per result.
        :param enrich_profile: Whether to return profile enrichment.
        :param enrich_targeting: Whether to return targeting enrichment.
        :param enrich_history: Whether to return history enrichment.
        :param enrich_signals: Whether to return signal enrichment.
        :param enrich_vectors: Whether to return vector enrichment.
        :return: Rich search results.
        """
        payload = without_none(
            question=question,
            instruction=instruction,
            expansions=expansions,
            sql_filter=sql_filter,
            algorithm=algorithm,
            min_similarity=min_similarity,
            must_include=must_include,
            must_exclude=must_exclude,
            brand_safety=brand_safety,
            language=language,
            continent=continent,
            region=region,
            country=country,
            sector=sector,
            industry_group=industry_group,
            industry=industry,
            sub_industry=sub_industry,
            iab_tier_1=iab_tier_1,
            iab_tier_2=iab_tier_2,
            iab_tier_3=iab_tier_3,
            iab_tier_4=iab_tier_4,
            companies=companies,
            collection=collection,
            deduplicate=deduplicate,
            internal_use=internal_use,
            n_results=n_results,
            n_probes=n_probes,
            n_contextify=n_contextify,
            enrich_profile=enrich_profile,
            enrich_targeting=enrich_targeting,
            enrich_history=enrich_history,
            enrich_signals=enrich_signals,
            enrich_vectors=enrich_vectors
        )
        validate_search_common(
            payload=payload,
            result_bounds=(10, 100),
            probe_bounds=(5, 50),
            context_bounds=(64, 1024)
        )
        for name in (
            "enrich_profile",
            "enrich_targeting",
            "enrich_history",
            "enrich_signals",
            "enrich_vectors"
        ):
            if not isinstance(payload[name], bool):
                raise ValueError(f"{name} must be a boolean")
        data = self.search_json(
            endpoint="rich-search",
            payload=payload
        )
        response = data.get("response", [])
        if not isinstance(response, list):
            raise ValueError("rich-search response must be a list")
        return ResultSet(
            results=[
                RichResult.from_dict(data=item)
                for item in response
            ],
            message=data.get("message"),
            query=data.get("query")
        )

    def bulk_search(
        self: "Nosible",
        search: Optional[Search] = None,
        question: Optional[str] = None,
        expansions: Optional[List[str]] = None,
        sql_filter: Optional[str] = None,
        n_results: int = 1000,
        n_probes: int = 10,
        n_contextify: int = 128,
        algorithm: str = "hybrid-3",
        min_similarity: Optional[float] = None,
        must_include: Optional[List[str]] = None,
        must_exclude: Optional[List[str]] = None,
        brand_safety: Optional[str] = None,
        language: Optional[str] = None,
        continent: Optional[str] = None,
        region: Optional[str] = None,
        country: Optional[str] = None,
        sector: Optional[str] = None,
        industry_group: Optional[str] = None,
        industry: Optional[str] = None,
        sub_industry: Optional[str] = None,
        iab_tier_1: Optional[str] = None,
        iab_tier_2: Optional[str] = None,
        iab_tier_3: Optional[str] = None,
        iab_tier_4: Optional[str] = None,
        instruction: Optional[str] = None,
        companies: Optional[List[str]] = None,
        collection: Optional[str] = None,
        deduplicate: Optional[bool] = None,
        internal_use: Optional[Dict[str, Any]] = None,
        poll_interval: float = 15,
        poll_timeout: float = 1500,
        verbose: bool = False,
        autogenerate_expansions: bool = False,
        publish_start: Optional[str] = None,
        publish_end: Optional[str] = None,
        include_netlocs: Optional[List[str]] = None,
        exclude_netlocs: Optional[List[str]] = None,
        visited_start: Optional[str] = None,
        visited_end: Optional[str] = None,
        certain: Optional[bool] = None,
        include_companies: Optional[List[str]] = None,
        exclude_companies: Optional[List[str]] = None,
        include_docs: Optional[List[str]] = None,
        exclude_docs: Optional[List[str]] = None,
        **kwargs: Any
    ) -> ResultSet:
        """
        Run asynchronous Bulk Search and download its encrypted result archive.

        :param search: Optional Search model.
        :param question: Search question.
        :param expansions: Query expansions.
        :param sql_filter: SQL filter.
        :param n_results: Requested result count.
        :param n_probes: Number of search probes.
        :param n_contextify: Context size per result.
        :param algorithm: Retrieval algorithm.
        :param min_similarity: Minimum similarity score.
        :param must_include: Required strings.
        :param must_exclude: Forbidden strings.
        :param brand_safety: Brand-safety filter.
        :param language: ISO language filter.
        :param continent: Continent filter.
        :param region: Region filter.
        :param country: Country filter.
        :param sector: GICS sector filter.
        :param industry_group: GICS industry-group filter.
        :param industry: GICS industry filter.
        :param sub_industry: GICS sub-industry filter.
        :param iab_tier_1: IAB tier-one filter.
        :param iab_tier_2: IAB tier-two filter.
        :param iab_tier_3: IAB tier-three filter.
        :param iab_tier_4: IAB tier-four filter.
        :param instruction: Retrieval instruction.
        :param companies: Company names to refine retrieval.
        :param collection: Search collection.
        :param deduplicate: Whether to remove duplicate headlines.
        :param internal_use: Private feature controls.
        :param poll_interval: Download polling interval in seconds.
        :param poll_timeout: Maximum polling duration in seconds.
        :param verbose: Retained compatibility flag.
        :param autogenerate_expansions: Whether to generate LLM expansions.
        :param publish_start: Earliest publication date.
        :param publish_end: Latest publication date.
        :param include_netlocs: Domains to include.
        :param exclude_netlocs: Domains to exclude.
        :param visited_start: Earliest visit date.
        :param visited_end: Latest visit date.
        :param certain: Whether dates must be certain.
        :param include_companies: Company identifiers to include.
        :param exclude_companies: Company identifiers to exclude.
        :param include_docs: Document hashes to include.
        :param exclude_docs: Document hashes to exclude.
        :param kwargs: Deprecated language-list filters.
        :return: Downloaded bulk results.
        """
        warn_legacy_language_filters(kwargs=kwargs)
        if verbose:
            LOGGER.info(msg="Submitting NOSIBLE Bulk Search")
        payload = self.search_payload(
            search=search,
            question=question,
            instruction=instruction,
            expansions=expansions,
            sql_filter=sql_filter,
            algorithm=algorithm,
            min_similarity=min_similarity,
            must_include=must_include,
            must_exclude=must_exclude,
            brand_safety=brand_safety,
            language=language,
            continent=continent,
            region=region,
            country=country,
            sector=sector,
            industry_group=industry_group,
            industry=industry,
            sub_industry=sub_industry,
            iab_tier_1=iab_tier_1,
            iab_tier_2=iab_tier_2,
            iab_tier_3=iab_tier_3,
            iab_tier_4=iab_tier_4,
            companies=companies,
            collection=collection,
            deduplicate=deduplicate,
            internal_use=internal_use,
            n_results=n_results,
            n_probes=n_probes,
            n_contextify=n_contextify,
            autogenerate_expansions=autogenerate_expansions,
            legacy_filters={
                "publish_start": (
                    publish_start
                    if publish_start is not None
                    else self.publish_start
                ),
                "publish_end": (
                    publish_end
                    if publish_end is not None
                    else self.publish_end
                ),
                "include_netlocs": (
                    include_netlocs
                    if include_netlocs is not None
                    else self.include_netlocs
                ),
                "exclude_netlocs": (
                    exclude_netlocs
                    if exclude_netlocs is not None
                    else self.exclude_netlocs
                ),
                "visited_start": (
                    visited_start
                    if visited_start is not None
                    else self.visited_start
                ),
                "visited_end": (
                    visited_end
                    if visited_end is not None
                    else self.visited_end
                ),
                "certain": certain if certain is not None else self.certain,
                "include_companies": (
                    include_companies
                    if include_companies is not None
                    else self.include_companies
                ),
                "exclude_companies": (
                    exclude_companies
                    if exclude_companies is not None
                    else self.exclude_companies
                ),
                "include_docs": (
                    include_docs
                    if include_docs is not None
                    else self.include_docs
                ),
                "exclude_docs": (
                    exclude_docs
                    if exclude_docs is not None
                    else self.exclude_docs
                ),
            }
        )
        validate_search_common(
            payload=payload,
            result_bounds=(1000, 10000),
            probe_bounds=(5, 300),
            context_bounds=(128, 1024)
        )
        data = self.downloaded_search(
            endpoint="bulk-search",
            payload=payload,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout
        )
        return ResultSet.from_dict(data=data)

    def time_search(
        self: "Nosible",
        start: str,
        end: str,
        frequency: str = "1d",
        sort: str = "ascending",
        require_timezone: bool = False,
        n_results: int = 25,
        n_probes: int = 10,
        n_contextify: int = 128,
        question: Optional[str] = None,
        instruction: Optional[str] = None,
        expansions: Optional[List[str]] = None,
        sql_filter: Optional[str] = None,
        algorithm: Optional[str] = None,
        min_similarity: Optional[float] = None,
        must_include: Optional[List[str]] = None,
        must_exclude: Optional[List[str]] = None,
        companies: Optional[List[str]] = None,
        collection: Optional[str] = None,
        deduplicate: Optional[bool] = None,
        internal_use: Optional[Dict[str, Any]] = None,
        poll_interval: float = 15,
        poll_timeout: float = 1500,
        **filters: Any
    ) -> Dict[str, Any]:
        """
        Run independent searches across a time interval.

        :param start: Inclusive timezone-aware ISO start timestamp.
        :param end: Exclusive timezone-aware ISO end timestamp.
        :param frequency: Positive h, d, w, or mo interval.
        :param sort: Result order, ascending or descending.
        :param require_timezone: Whether results must expose timezone data.
        :param n_results: Results requested per interval.
        :param n_probes: Number of search probes.
        :param n_contextify: Context size per result.
        :param question: Optional Search question.
        :param instruction: Retrieval instruction.
        :param expansions: Query expansions.
        :param sql_filter: SQL filter.
        :param algorithm: Retrieval algorithm.
        :param min_similarity: Minimum similarity score.
        :param must_include: Required strings.
        :param must_exclude: Forbidden strings.
        :param companies: Company names to refine retrieval.
        :param collection: Search collection.
        :param deduplicate: Whether to remove duplicate headlines.
        :param internal_use: Private feature controls.
        :param poll_interval: Download polling interval in seconds.
        :param poll_timeout: Maximum polling duration in seconds.
        :param filters: Additional inherited Search filters.
        :return: Downloaded time-search response.
        """
        start_datetime = parse_datetime(
            value=start,
            name="start"
        )
        end_datetime = parse_datetime(
            value=end,
            name="end"
        )
        if start_datetime >= end_datetime:
            raise ValueError("start must be earlier than end")
        if (
            not isinstance(frequency, str)
            or not 2 <= len(frequency) <= 8
            or not re.fullmatch(
                pattern=r"[1-9]\d*(?:h|d|w|mo)",
                string=frequency
            )
        ):
            raise ValueError(
                "frequency must use a positive h, d, w, or mo unit"
            )
        if sort not in {
            "ascending",
            "descending"
        }:
            raise ValueError("sort must be 'ascending' or 'descending'")
        payload = without_none(
            start=start,
            end=end,
            frequency=frequency,
            sort=sort,
            require_timezone=require_timezone,
            n_results=n_results,
            n_probes=n_probes,
            n_contextify=n_contextify,
            question=question,
            instruction=instruction,
            expansions=expansions,
            sql_filter=sql_filter,
            algorithm=algorithm,
            min_similarity=min_similarity,
            must_include=must_include,
            must_exclude=must_exclude,
            companies=companies,
            collection=collection,
            deduplicate=deduplicate,
            internal_use=internal_use,
            **filters
        )
        validate_search_common(
            payload=payload,
            result_bounds=(1, 1000),
            probe_bounds=(5, 300),
            context_bounds=(128, 1024)
        )
        search_count = time_bucket_count(
            start=start_datetime,
            end=end_datetime,
            frequency=frequency
        )
        if search_count > 500:
            raise ValueError(
                "time search cannot exceed 500 interval buckets"
            )
        if search_count * n_results > 50_000:
            raise ValueError(
                "time search cannot request more than 50,000 total results"
            )
        return self.downloaded_search(
            endpoint="time-search",
            payload=payload,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout
        )

    def scrape_url(
        self: "Nosible",
        html: str = "",
        recrawl: bool = False,
        render: bool = False,
        url: Optional[str] = None
    ) -> WebPageData:
        """
        Scrape a URL or supplied HTML document.

        :param html: Optional raw HTML.
        :param recrawl: Whether to force a fresh crawl.
        :param render: Whether to render JavaScript.
        :param url: URL to scrape.
        :return: Structured web-page data.
        """
        if url is None and not html:
            raise TypeError("Specify a URL or HTML document")
        data = self.search_json(
            endpoint="scrape-url",
            payload=without_none(
                url=url,
                html=html,
                render=render,
                recrawl=recrawl
            )
        )
        response = data.get("response")
        if not isinstance(response, dict):
            raise ValueError(
                "scrape-url response is missing its response object"
            )
        return WebPageData(
            full_text=response.get("full_text"),
            languages=response.get("languages"),
            metadata=response.get("metadata"),
            page=response.get("page"),
            request=response.get("request"),
            snippets=SnippetSet.from_dict(
                data=response.get("snippets", {})
            ),
            statistics=response.get("statistics"),
            structured=response.get("structured"),
            url_tree=response.get("url_tree")
        )

    def topic_trend(
        self: "Nosible",
        query: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sql_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Return daily trend values for a topic.

        :param query: Topic query from 5 to 100 characters.
        :param start_date: Optional inclusive first date.
        :param end_date: Optional inclusive final date.
        :param sql_filter: Optional Search SQL filter.
        :return: Date-keyed trend values.
        """
        if start_date is not None:
            validate_date_format(
                value=start_date,
                name="start_date"
            )
        if end_date is not None:
            validate_date_format(
                value=end_date,
                name="end_date"
            )
        if not isinstance(query, str) or not 5 <= len(query) <= 100:
            raise ValueError(
                "query must contain between 5 and 100 characters"
            )
        data = self.search_json(
            endpoint="topic-trend",
            payload={
                "query": query,
                "sql_filter": (
                    sql_filter or "SELECT loc, published FROM engine"
                )
            }
        )
        response = data.get("response")
        if not isinstance(response, dict):
            raise ValueError("topic-trend response must be an object")
        return {
            date: value
            for date, value in response.items()
            if (
                start_date is None
                or date >= start_date
            )
            and (
                end_date is None
                or date <= end_date
            )
        }

    def save_search(
        self: "Nosible",
        **values: Any
    ) -> Dict[str, Any]:
        """
        Save a Search definition.

        :param values: Saved Search fields.
        :return: Saved Search response.
        """
        payload = without_none(**values)
        validate_search_common(
            payload=payload,
            result_bounds=(10, 100),
            probe_bounds=(5, 1000),
            context_bounds=(64, 1024),
            algorithms=frozenset({"hybrid-3"})
        )
        return self.search_json(
            endpoint="save-search",
            payload=payload
        )

    def get_searches(
        self: "Nosible"
    ) -> Dict[str, Any]:
        """
        Return saved Searches.

        :return: Saved Search response.
        """
        return self.search_json(
            endpoint="get-searches",
            payload={}
        )

    def delete_search(
        self: "Nosible",
        search_id: str
    ) -> Dict[str, Any]:
        """
        Delete a saved Search.

        :param search_id: Saved Search identifier.
        :return: Deletion response.
        """
        if not isinstance(search_id, str) or not search_id:
            raise ValueError("search_id must be a non-empty string")
        return self.search_json(
            endpoint="delete-search",
            payload={
                "search_id": search_id
            }
        )

    def get_limits(
        self: "Nosible"
    ) -> Dict[str, Any]:
        """
        Return Search limits for the current API key.

        :return: Search limit response.
        """
        data = self.transport.request_json(
            method="GET",
            path="search/v2/limits",
            auth="search"
        )
        if not isinstance(data, dict) or not isinstance(
            data.get("limits"),
            list
        ):
            raise ValueError("limits response has an invalid shape")
        return data

    def answer(
        self: "Nosible",
        query: str,
        n_results: int = 100,
        min_similarity: float = 0.65,
        model: Optional[str] = "google/gemini-2.0-flash-001",
        show_context: bool = True
    ) -> str:
        """
        Answer a question using Fast Search results as context.

        :param query: Natural-language question.
        :param n_results: Results used as context.
        :param min_similarity: Minimum context similarity.
        :param model: OpenAI-compatible model name.
        :param show_context: Whether to print the assembled context.
        :return: LLM answer.
        """
        if not self.llm_api_key:
            raise ValueError("An LLM API key is required for answer().")
        results = self.fast_search(
            question=query,
            n_results=n_results,
            min_similarity=min_similarity
        )
        context_parts = []
        for index, result in enumerate(results):
            similarity = (
                result.similarity * 100
                if result.similarity is not None
                else 0
            )
            context_parts.append(
                "\n".join(
                    [
                        f"Doc {index + 1}",
                        f"Title: {result.title}",
                        f"Similarity Score: {similarity:.2f}%",
                        f"URL: {result.url}",
                        f"Content: {result.content}"
                    ]
                )
            )
        context = "\n\n".join(context_parts)
        if show_context:
            print(textwrap.dedent(text=context))
        prompt = (
            "Use the context to answer the question. Cite document labels in "
            f"square brackets.\n\nQuestion:\n{query}\n\nContext:\n{context}"
        )
        llm_client = OpenAI(
            base_url=self.openai_base_url,
            api_key=self.llm_api_key
        )
        try:
            response = llm_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        except OpenAIError as error:
            raise RuntimeError(f"LLM API error: {error}") from error
        choices = getattr(response, "choices", None)
        if not choices or not hasattr(choices[0], "message"):
            raise RuntimeError(f"Invalid LLM response format: {response!r}")
        return "Answer:\n" + choices[0].message.content.strip()

    def fast_search(
        self: "Nosible",
        search: Optional[Search] = None,
        question: Optional[str] = None,
        expansions: Optional[List[str]] = None,
        sql_filter: Optional[str] = None,
        n_results: int = 100,
        n_probes: int = 30,
        n_contextify: int = 128,
        algorithm: str = "hybrid-3",
        min_similarity: Optional[float] = None,
        must_include: Optional[List[str]] = None,
        must_exclude: Optional[List[str]] = None,
        autogenerate_expansions: bool = False,
        publish_start: Optional[str] = None,
        publish_end: Optional[str] = None,
        include_netlocs: Optional[List[str]] = None,
        exclude_netlocs: Optional[List[str]] = None,
        visited_start: Optional[str] = None,
        visited_end: Optional[str] = None,
        certain: Optional[bool] = None,
        include_companies: Optional[List[str]] = None,
        exclude_companies: Optional[List[str]] = None,
        include_docs: Optional[List[str]] = None,
        exclude_docs: Optional[List[str]] = None,
        brand_safety: Optional[str] = None,
        language: Optional[str] = None,
        continent: Optional[str] = None,
        region: Optional[str] = None,
        country: Optional[str] = None,
        sector: Optional[str] = None,
        industry_group: Optional[str] = None,
        industry: Optional[str] = None,
        sub_industry: Optional[str] = None,
        iab_tier_1: Optional[str] = None,
        iab_tier_2: Optional[str] = None,
        iab_tier_3: Optional[str] = None,
        iab_tier_4: Optional[str] = None,
        instruction: Optional[str] = None,
        companies: Optional[List[str]] = None,
        collection: Optional[str] = None,
        deduplicate: Optional[bool] = None,
        internal_use: Optional[Dict[str, Any]] = None,
        *args: Any,
        **kwargs: Any
    ) -> ResultSet:
        """
        Run interactive Fast Search.

        :param search: Optional Search model.
        :param question: Search question.
        :param expansions: Query expansions.
        :param sql_filter: SQL filter.
        :param n_results: Requested result count.
        :param n_probes: Number of search probes.
        :param n_contextify: Context size per result.
        :param algorithm: Retrieval algorithm.
        :param min_similarity: Minimum similarity score.
        :param must_include: Required strings.
        :param must_exclude: Forbidden strings.
        :param autogenerate_expansions: Whether to generate LLM expansions.
        :param publish_start: Earliest publication date.
        :param publish_end: Latest publication date.
        :param include_netlocs: Domains to include.
        :param exclude_netlocs: Domains to exclude.
        :param visited_start: Earliest visit date.
        :param visited_end: Latest visit date.
        :param certain: Whether dates must be certain.
        :param include_companies: Company identifiers to include.
        :param exclude_companies: Company identifiers to exclude.
        :param include_docs: Document hashes to include.
        :param exclude_docs: Document hashes to exclude.
        :param brand_safety: Brand-safety filter.
        :param language: ISO language filter.
        :param continent: Continent filter.
        :param region: Region filter.
        :param country: Country filter.
        :param sector: GICS sector filter.
        :param industry_group: GICS industry-group filter.
        :param industry: GICS industry filter.
        :param sub_industry: GICS sub-industry filter.
        :param iab_tier_1: IAB tier-one filter.
        :param iab_tier_2: IAB tier-two filter.
        :param iab_tier_3: IAB tier-three filter.
        :param iab_tier_4: IAB tier-four filter.
        :param instruction: Retrieval instruction.
        :param companies: Company names to refine retrieval.
        :param collection: Search collection.
        :param deduplicate: Whether to remove duplicate headlines.
        :param internal_use: Private feature controls.
        :param args: Ignored legacy positional arguments.
        :param kwargs: Deprecated language-list filters.
        :return: Interactive search results.
        """
        if args:
            warnings.warn(
                message="Additional positional arguments are ignored",
                category=DeprecationWarning,
                stacklevel=2
            )
        warn_legacy_language_filters(kwargs=kwargs)
        requested_results = (
            search.n_results
            if search is not None and search.n_results is not None
            else n_results
        )
        if (
            isinstance(requested_results, bool)
            or not isinstance(requested_results, int)
            or not 1 <= requested_results <= 100
        ):
            raise ValueError("n_results must be between 1 and 100")
        wire_results = max(10, requested_results)
        payload = self.search_payload(
            search=search,
            question=question,
            instruction=instruction,
            expansions=expansions,
            sql_filter=sql_filter,
            algorithm=algorithm,
            min_similarity=min_similarity,
            must_include=must_include,
            must_exclude=must_exclude,
            brand_safety=brand_safety,
            language=language,
            continent=continent,
            region=region,
            country=country,
            sector=sector,
            industry_group=industry_group,
            industry=industry,
            sub_industry=sub_industry,
            iab_tier_1=iab_tier_1,
            iab_tier_2=iab_tier_2,
            iab_tier_3=iab_tier_3,
            iab_tier_4=iab_tier_4,
            companies=companies,
            collection=collection,
            deduplicate=deduplicate,
            internal_use=internal_use,
            n_results=wire_results,
            n_probes=n_probes,
            n_contextify=n_contextify,
            autogenerate_expansions=autogenerate_expansions,
            legacy_filters={
                "publish_start": (
                    publish_start
                    if publish_start is not None
                    else self.publish_start
                ),
                "publish_end": (
                    publish_end
                    if publish_end is not None
                    else self.publish_end
                ),
                "include_netlocs": (
                    include_netlocs
                    if include_netlocs is not None
                    else self.include_netlocs
                ),
                "exclude_netlocs": (
                    exclude_netlocs
                    if exclude_netlocs is not None
                    else self.exclude_netlocs
                ),
                "visited_start": (
                    visited_start
                    if visited_start is not None
                    else self.visited_start
                ),
                "visited_end": (
                    visited_end
                    if visited_end is not None
                    else self.visited_end
                ),
                "certain": certain if certain is not None else self.certain,
                "include_companies": (
                    include_companies
                    if include_companies is not None
                    else self.include_companies
                ),
                "exclude_companies": (
                    exclude_companies
                    if exclude_companies is not None
                    else self.exclude_companies
                ),
                "include_docs": (
                    include_docs
                    if include_docs is not None
                    else self.include_docs
                ),
                "exclude_docs": (
                    exclude_docs
                    if exclude_docs is not None
                    else self.exclude_docs
                ),
            }
        )
        payload["n_results"] = wire_results
        validate_search_common(
            payload=payload,
            result_bounds=(10, 100),
            probe_bounds=(5, 50),
            context_bounds=(64, 1024)
        )
        data = self.search_json(
            endpoint="fast-search",
            payload=payload
        )
        result_set = ResultSet.from_dict(data=data)
        if requested_results < len(result_set):
            object.__setattr__(
                result_set,
                "results",
                result_set.results[:requested_results]
            )
        return result_set

    def close(
        self: "Nosible"
    ) -> None:
        """
        Close resources owned by this client.

        :return: None.
        """
        if self.closed:
            return
        self.closed = True
        if self.owns_http_client:
            self.session.close()

    def search_payload(
        self: "Nosible",
        search: Optional[Search],
        question: Optional[str],
        instruction: Optional[str],
        expansions: Optional[List[str]],
        sql_filter: Optional[str],
        algorithm: Optional[str],
        min_similarity: Optional[float],
        must_include: Optional[List[str]],
        must_exclude: Optional[List[str]],
        brand_safety: Optional[str],
        language: Optional[str],
        continent: Optional[str],
        region: Optional[str],
        country: Optional[str],
        sector: Optional[str],
        industry_group: Optional[str],
        industry: Optional[str],
        sub_industry: Optional[str],
        iab_tier_1: Optional[str],
        iab_tier_2: Optional[str],
        iab_tier_3: Optional[str],
        iab_tier_4: Optional[str],
        companies: Optional[List[str]],
        collection: Optional[str],
        deduplicate: Optional[bool],
        internal_use: Optional[Dict[str, Any]],
        n_results: Optional[int],
        n_probes: Optional[int],
        n_contextify: Optional[int],
        autogenerate_expansions: bool,
        legacy_filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge direct, model, generated, and legacy Search fields.

        :param search: Optional Search model.
        :param question: Direct Search question.
        :param instruction: Retrieval instruction.
        :param expansions: Query expansions.
        :param sql_filter: SQL filter.
        :param algorithm: Retrieval algorithm.
        :param min_similarity: Minimum similarity score.
        :param must_include: Required strings.
        :param must_exclude: Forbidden strings.
        :param brand_safety: Brand-safety filter.
        :param language: ISO language filter.
        :param continent: Continent filter.
        :param region: Region filter.
        :param country: Country filter.
        :param sector: GICS sector filter.
        :param industry_group: GICS industry-group filter.
        :param industry: GICS industry filter.
        :param sub_industry: GICS sub-industry filter.
        :param iab_tier_1: IAB tier-one filter.
        :param iab_tier_2: IAB tier-two filter.
        :param iab_tier_3: IAB tier-three filter.
        :param iab_tier_4: IAB tier-four filter.
        :param companies: Company names to refine retrieval.
        :param collection: Search collection.
        :param deduplicate: Whether to remove duplicate headlines.
        :param internal_use: Private feature controls.
        :param n_results: Requested result count.
        :param n_probes: Number of search probes.
        :param n_contextify: Context size per result.
        :param autogenerate_expansions: Whether to generate expansions.
        :param legacy_filters: Structured legacy filters.
        :return: Search API request payload.
        """
        if search is not None and question is not None:
            raise TypeError(
                "Specify exactly one of 'question' or 'search'."
            )
        if search is None and question is None:
            raise TypeError(
                "Specify exactly one of 'question' or 'search'."
            )
        direct = without_none(
            question=question,
            instruction=instruction,
            expansions=expansions,
            sql_filter=sql_filter,
            algorithm=algorithm,
            min_similarity=min_similarity,
            must_include=must_include,
            must_exclude=must_exclude,
            brand_safety=brand_safety,
            language=language,
            continent=continent,
            region=region,
            country=country,
            sector=sector,
            industry_group=industry_group,
            industry=industry,
            sub_industry=sub_industry,
            iab_tier_1=iab_tier_1,
            iab_tier_2=iab_tier_2,
            iab_tier_3=iab_tier_3,
            iab_tier_4=iab_tier_4,
            companies=companies,
            collection=collection,
            deduplicate=deduplicate,
            internal_use=internal_use,
            n_results=n_results,
            n_probes=n_probes,
            n_contextify=n_contextify
        )
        if search is not None:
            source = {
                key: value
                for key, value in search.to_dict().items()
                if value is not None
            }
            for key, value in direct.items():
                source.setdefault(key, value)
        else:
            source = direct
        source.pop("autogenerate_expansions", None)
        legacy_names = (
            "publish_start",
            "publish_end",
            "visited_start",
            "visited_end",
            "certain",
            "include_netlocs",
            "exclude_netlocs",
            "include_companies",
            "exclude_companies",
            "include_docs",
            "exclude_docs"
        )
        effective_legacy_filters = dict(legacy_filters)
        for legacy_name in legacy_names:
            if legacy_name in source:
                effective_legacy_filters[legacy_name] = source[legacy_name]
            source.pop(legacy_name, None)
        should_generate = autogenerate_expansions or bool(
            getattr(search, "autogenerate_expansions", False)
        )
        if should_generate and not source.get("expansions"):
            source["expansions"] = self.generate_expansions(
                question=source["question"]
            )
        if source.get("sql_filter") is None and any(
            value is not None
            for value in effective_legacy_filters.values()
        ):
            source["sql_filter"] = self.format_sql(**effective_legacy_filters)
        return source

    def generate_expansions(
        self: "Nosible",
        question: Union[str, Search]
    ) -> List[str]:
        """
        Generate ten semantically equivalent Search questions.

        :param question: Source question or Search model.
        :return: Ten generated query expansions.
        """
        if not self.llm_api_key:
            raise ValueError(
                "LLM API key is required for generating expansions."
            )
        question_text = (
            question.question
            if isinstance(question, Search)
            else question
        )
        if not isinstance(question_text, str) or not question_text:
            raise ValueError("question must be a non-empty string")
        prompt = (
            "Return a JSON list of exactly ten semantically equivalent, "
            "lexically diverse questions for this search query:\n"
            f"{question_text}"
        )
        llm_client = OpenAI(
            base_url=self.openai_base_url,
            api_key=self.llm_api_key
        )
        response = llm_client.chat.completions.create(
            model=self.expansions_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )
        raw_response = response.choices[0].message.content.strip()
        if raw_response.startswith("```"):
            raw_response = raw_response.strip("`").strip()
            if raw_response.lower().startswith("json"):
                raw_response = raw_response[4:].strip()
        try:
            expansions = json.loads(s=raw_response)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                "OpenAI-compatible response was not valid JSON"
            ) from error
        if (
            not isinstance(expansions, list)
            or len(expansions) != 10
            or any(
                not isinstance(expansion, str)
                for expansion in expansions
            )
        ):
            raise RuntimeError(
                "Expansion response must contain exactly ten strings"
            )
        return expansions

    def format_sql(
        self: "Nosible",
        publish_start: Optional[str] = None,
        publish_end: Optional[str] = None,
        visited_start: Optional[str] = None,
        visited_end: Optional[str] = None,
        certain: Optional[bool] = None,
        include_netlocs: Optional[List[str]] = None,
        exclude_netlocs: Optional[List[str]] = None,
        include_companies: Optional[List[str]] = None,
        exclude_companies: Optional[List[str]] = None,
        include_docs: Optional[List[str]] = None,
        exclude_docs: Optional[List[str]] = None
    ) -> str:
        """
        Build the legacy SQL filter from structured filter values.

        :param publish_start: Earliest publication date.
        :param publish_end: Latest publication date.
        :param visited_start: Earliest visit date.
        :param visited_end: Latest visit date.
        :param certain: Whether dates must be certain.
        :param include_netlocs: Domains to include.
        :param exclude_netlocs: Domains to exclude.
        :param include_companies: Company identifiers to include.
        :param exclude_companies: Company identifiers to exclude.
        :param include_docs: Document hashes to include.
        :param exclude_docs: Document hashes to exclude.
        :return: Valid Search SQL filter.
        """
        date_values = {
            "publish_start": publish_start,
            "publish_end": publish_end,
            "visited_start": visited_start,
            "visited_end": visited_end
        }
        for name, value in date_values.items():
            if value is not None:
                validate_date_format(
                    value=value,
                    name=name
                )
        list_values = {
            "include_netlocs": include_netlocs,
            "exclude_netlocs": exclude_netlocs,
            "include_companies": include_companies,
            "exclude_companies": exclude_companies,
            "include_docs": include_docs,
            "exclude_docs": exclude_docs
        }
        for name, values in list_values.items():
            if values is not None and len(values) > 50:
                raise ValueError(
                    f"{name} cannot contain more than 50 items"
                )

        clauses = []
        append_date_clause(
            clauses=clauses,
            column="published",
            start=publish_start,
            end=publish_end
        )
        append_date_clause(
            clauses=clauses,
            column="visited",
            start=visited_start,
            end=visited_end
        )
        if certain is not None:
            clauses.append(
                "certain = TRUE"
                if certain
                else "certain = FALSE"
            )
        append_netloc_clause(
            clauses=clauses,
            values=include_netlocs,
            include=True
        )
        append_netloc_clause(
            clauses=clauses,
            values=exclude_netlocs,
            include=False
        )
        append_array_clause(
            clauses=clauses,
            values=include_companies,
            include=True
        )
        append_array_clause(
            clauses=clauses,
            values=exclude_companies,
            include=False
        )
        append_document_clause(
            clauses=clauses,
            values=include_docs,
            include=True
        )
        append_document_clause(
            clauses=clauses,
            values=exclude_docs,
            include=False
        )
        sql = "SELECT loc FROM engine"
        if clauses:
            sql = f"{sql} WHERE {' AND '.join(clauses)}"
        if not self.validate_sql(sql=sql):
            raise ValueError(f"Invalid SQL query: {sql!r}")
        return sql

    def validate_sql(
        self: "Nosible",
        sql: str
    ) -> bool:
        """
        Validate Search SQL against the supported engine schema.

        :param sql: SQL query to validate.
        :return: Whether Polars accepts the SQL against the engine schema.
        """
        columns = [
            "loc",
            "published",
            "visited",
            "certain",
            "netloc",
            "language",
            "companies",
            "doc"
        ]
        frame = pl.DataFrame(
            data={
                column: []
                for column in columns
            }
        )
        context = pl.SQLContext()
        context.register(
            name="engine",
            frame=frame
        )
        try:
            context.execute(query=sql)
            return True
        except pl.exceptions.PolarsError:
            return False

    def downloaded_search(
        self: "Nosible",
        endpoint: str,
        payload: Dict[str, Any],
        poll_interval: float,
        poll_timeout: float
    ) -> Dict[str, Any]:
        """
        Poll and decode an encrypted Search download.

        :param endpoint: Bulk or Time Search endpoint suffix.
        :param payload: Search request body.
        :param poll_interval: Polling interval in seconds.
        :param poll_timeout: Maximum polling duration in seconds.
        :return: Decoded Search response.
        """
        if poll_interval < 0 or poll_timeout < 0:
            raise ValueError(
                "poll_interval and poll_timeout cannot be negative"
            )
        accepted = self.search_json(
            endpoint=endpoint,
            payload=payload
        )
        download_from = accepted.get("download_from")
        decrypt_using = accepted.get("decrypt_using")
        if not isinstance(download_from, str) or not isinstance(
            decrypt_using,
            str
        ):
            raise ValueError(
                f"{endpoint} did not return download credentials"
            )
        deadline = time.monotonic() + poll_timeout
        while True:
            response = self.transport.download(url=download_from)
            if response.status_code == 200:
                return decode_download(
                    content=response.content,
                    key=decrypt_using
                )
            if not pending_download_response(
                response=response,
                url=download_from
            ):
                raise error_from_response(response=response)
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Timed out waiting for {endpoint} results after "
                    f"{poll_timeout} seconds"
                )
            if poll_interval:
                time.sleep(
                    min(
                        poll_interval,
                        max(
                            0,
                            deadline - time.monotonic()
                        )
                    )
                )

    def search_json(
        self: "Nosible",
        endpoint: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Post to a Search v2.1 endpoint and require an object response.

        :param endpoint: Search endpoint suffix.
        :param payload: JSON request body.
        :return: JSON response object.
        """
        data = self.transport.request_json(
            method="POST",
            path=f"search/v2/{endpoint}",
            auth="search",
            json=payload
        )
        if not isinstance(data, dict):
            raise ValueError(f"{endpoint} returned a non-object response")
        return data


def pending_download_response(
    response: httpx.Response,
    url: str
) -> bool:
    """
    Identify an object-storage response that means the archive is not ready.

    Some NOSIBLE deployments return an unsigned object-storage URL. While the
    asynchronous result is being written, Wasabi responds with an XML 403
    ``AccessDenied`` rather than the 404 used by other deployments. A signed
    URL returning 403 remains an actual access error and is not retried.

    :param response: Download response.
    :param url: Download URL supplied by NOSIBLE.
    :return: Whether polling should continue.
    """
    if response.status_code == 404:
        return True
    return (
        response.status_code == 403
        and not urlsplit(url=url).query
        and re.search(
            pattern=r"<Code>\s*AccessDenied\s*</Code>",
            string=response.text
        ) is not None
    )


def without_none(
    **values: Any
) -> Dict[str, Any]:
    """
    Remove None-valued fields from a dictionary.

    :param values: Candidate fields.
    :return: Fields whose values are not None.
    """
    return {
        key: value
        for key, value in values.items()
        if value is not None
    }


def validate_search_common(
    payload: Dict[str, Any],
    result_bounds: Tuple[int, int],
    probe_bounds: Tuple[int, int],
    context_bounds: Tuple[int, int],
    algorithms: FrozenSet[str] = SEARCH_ALGORITHMS
) -> None:
    """
    Validate fields inherited by Search endpoint schemas.

    :param payload: Search request body.
    :param result_bounds: Inclusive result-count bounds.
    :param probe_bounds: Inclusive probe-count bounds.
    :param context_bounds: Inclusive context-size bounds.
    :param algorithms: Supported retrieval algorithms.
    :return: None.
    """
    validate_optional_text(
        payload=payload,
        name="question",
        minimum=1,
        maximum=500
    )
    validate_optional_text(
        payload=payload,
        name="instruction",
        minimum=1,
        maximum=500
    )
    for name, maximum in (
        ("expansions", 10),
        ("must_include", 100),
        ("must_exclude", 100),
        ("companies", 3)
    ):
        value = payload.get(name)
        if value is not None and (
            not isinstance(value, list)
            or len(value) > maximum
            or any(
                not isinstance(item, str)
                for item in value
            )
        ):
            raise ValueError(
                f"{name} must contain at most {maximum} strings"
            )
    if payload.get("collection") not in {
        None,
        "everything",
        "this-week"
    }:
        raise ValueError(
            "collection must be 'everything' or 'this-week'"
        )
    similarity = payload.get("min_similarity")
    if similarity is not None and (
        isinstance(similarity, bool)
        or not isinstance(similarity, (int, float))
        or not 0 <= similarity <= 1
    ):
        raise ValueError("min_similarity must be between 0 and 1")
    algorithm = payload.get("algorithm")
    if algorithm is not None and algorithm not in algorithms:
        raise ValueError(
            f"algorithm must be one of: {', '.join(sorted(algorithms))}"
        )
    brand_safety = payload.get("brand_safety")
    if (
        brand_safety is not None
        and brand_safety not in SEARCH_BRAND_SAFETY
    ):
        raise ValueError(
            "brand_safety must be Safe, Sensitive, or Unsafe"
        )
    language = payload.get("language")
    if language is not None and language not in SEARCH_LANGUAGES:
        raise ValueError(
            "language must be a supported ISO 639-1 code"
        )
    continent = payload.get("continent")
    if continent is not None and continent not in SEARCH_CONTINENTS:
        raise ValueError(
            "continent is not a supported NOSIBLE continent"
        )
    for name in (
        "deduplicate",
        "require_timezone"
    ):
        value = payload.get(name)
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"{name} must be a boolean")
    internal_use = payload.get("internal_use")
    if internal_use is not None and not isinstance(internal_use, dict):
        raise ValueError("internal_use must be an object")
    for name, bounds in (
        ("n_results", result_bounds),
        ("n_probes", probe_bounds),
        ("n_contextify", context_bounds)
    ):
        value = payload.get(name)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not bounds[0] <= value <= bounds[1]
        ):
            raise ValueError(
                f"{name} must be between {bounds[0]} and {bounds[1]}"
            )


def validate_optional_text(
    payload: Dict[str, Any],
    name: str,
    minimum: int,
    maximum: int
) -> None:
    """
    Validate an optional bounded text field.

    :param payload: Request body containing the field.
    :param name: Field name.
    :param minimum: Minimum length.
    :param maximum: Maximum length.
    :return: None.
    """
    value = payload.get(name)
    if value is not None and (
        not isinstance(value, str)
        or not minimum <= len(value) <= maximum
    ):
        raise ValueError(
            f"{name} must contain between {minimum} and {maximum} characters"
        )


def validate_date_format(
    value: str,
    name: str
) -> None:
    """
    Validate an ISO date or timestamp.

    :param value: Date or timestamp text.
    :param name: Parameter name for validation errors.
    :return: None.
    """
    if not isinstance(value, str) or re.match(
        pattern=r"^\d{4}-\d{2}-\d{2}",
        string=value
    ) is None:
        raise ValueError(
            f"Invalid date for '{name}': {value!r}. "
            "Expected ISO format 'YYYY-MM-DD'."
        )
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(
            f"Invalid date for '{name}': {value!r}. "
            "Expected ISO format 'YYYY-MM-DD'."
        ) from error


def parse_datetime(
    value: str,
    name: str
) -> datetime:
    """
    Parse a timezone-aware ISO timestamp.

    :param value: Timestamp text.
    :param name: Parameter name for validation errors.
    :return: Parsed timezone-aware timestamp.
    """
    if not isinstance(value, str):
        raise ValueError(
            f"{name} must be a timezone-aware ISO 8601 timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(
            f"{name} must be a timezone-aware ISO 8601 timestamp"
        ) from error
    if parsed.tzinfo is None:
        raise ValueError(f"{name} must include a timezone")
    return parsed


def time_bucket_count(
    start: datetime,
    end: datetime,
    frequency: str
) -> int:
    """
    Count Time Search intervals.

    :param start: Inclusive interval start.
    :param end: Exclusive interval end.
    :param frequency: Positive h, d, w, or mo interval.
    :return: Number of interval buckets.
    """
    match = re.fullmatch(
        pattern=r"([1-9]\d*)(h|d|w|mo)",
        string=frequency
    )
    if match is None:
        raise ValueError(
            "frequency must use a positive h, d, w, or mo unit"
        )
    amount = int(match.group(1))
    unit = match.group(2)
    if unit == "mo":
        count = 0
        while add_months(
            value=start,
            months=amount * count
        ) < end:
            count += 1
            if count > 500:
                break
        return count
    interval = {
        "h": timedelta(hours=amount),
        "d": timedelta(days=amount),
        "w": timedelta(weeks=amount)
    }[unit]
    return math.ceil((end - start) / interval)


def add_months(
    value: datetime,
    months: int
) -> datetime:
    """
    Add whole calendar months to a timestamp.

    :param value: Source timestamp.
    :param months: Month count to add.
    :return: Adjusted timestamp.
    """
    month_index = value.year * 12 + value.month - 1 + months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    day = min(
        value.day,
        monthrange(
            year=year,
            month=month
        )[1]
    )
    return value.replace(
        year=year,
        month=month,
        day=day
    )


def decode_download(
    content: bytes,
    key: str
) -> Dict[str, Any]:
    """
    Decrypt and decompress a Search result archive.

    :param content: Encrypted archive bytes.
    :param key: Fernet decryption key.
    :return: Decoded Search response.
    """
    try:
        decrypted = Fernet(
            key=key.encode(encoding="utf-8")
        ).decrypt(token=content)
    except (InvalidToken, ValueError, TypeError) as error:
        raise ValueError(
            "Unable to decrypt the NOSIBLE result payload"
        ) from error
    try:
        if decrypted.startswith(b"\x1f\x8b"):
            raw = gzip.decompress(data=decrypted)
        elif decrypted.startswith(b"\x28\xb5\x2f\xfd"):
            raw = zstandard.ZstdDecompressor().decompress(data=decrypted)
        else:
            raise ValueError("Unknown result compression format")
        data = json.loads(s=raw)
    except (
        ValueError,
        OSError,
        json.JSONDecodeError,
        zstandard.ZstdError
    ) as error:
        raise ValueError(
            "Unable to decode the NOSIBLE result payload"
        ) from error
    if not isinstance(data, dict) or not isinstance(
        data.get("response"),
        list
    ):
        raise ValueError(
            "Downloaded NOSIBLE results have an invalid shape"
        )
    return data


def warn_legacy_language_filters(
    kwargs: Dict[str, Any]
) -> None:
    """
    Warn when deprecated language-list filters are supplied.

    :param kwargs: Extra endpoint keyword arguments.
    :return: None.
    """
    if "include_languages" in kwargs or "exclude_languages" in kwargs:
        warnings.warn(
            message="Language list filters are deprecated; use 'language'",
            category=DeprecationWarning,
            stacklevel=3
        )


def append_date_clause(
    clauses: List[str],
    column: str,
    start: Optional[str],
    end: Optional[str]
) -> None:
    """
    Append a bounded SQL date clause.

    :param clauses: Mutable SQL clause collection.
    :param column: Date column name.
    :param start: Optional inclusive start.
    :param end: Optional inclusive end.
    :return: None.
    """
    if start and end:
        clauses.append(
            f"{column} >= {sql_literal(value=start)} "
            f"AND {column} <= {sql_literal(value=end)}"
        )
    elif start:
        clauses.append(f"{column} >= {sql_literal(value=start)}")
    elif end:
        clauses.append(f"{column} <= {sql_literal(value=end)}")


def append_netloc_clause(
    clauses: List[str],
    values: Optional[List[str]],
    include: bool
) -> None:
    """
    Append a SQL netloc membership clause.

    :param clauses: Mutable SQL clause collection.
    :param values: Domain values.
    :param include: Whether values are included or excluded.
    :return: None.
    """
    if not values:
        return
    variants = set()
    for value in values:
        variants |= {value}
        variants |= {
            value[4:]
            if value.startswith("www.")
            else f"www.{value}"
        }
    operator = "IN" if include else "NOT IN"
    literals = ", ".join(
        sql_literal(value=value)
        for value in sorted(variants)
    )
    clauses.append(f"netloc {operator} ({literals})")


def append_array_clause(
    clauses: List[str],
    values: Optional[List[str]],
    include: bool
) -> None:
    """
    Append a company-array membership clause.

    :param clauses: Mutable SQL clause collection.
    :param values: Company identifiers.
    :param include: Whether values are included or excluded.
    :return: None.
    """
    if not values:
        return
    checks = " OR ".join(
        f"ARRAY_CONTAINS(companies, {sql_literal(value=value)})"
        for value in values
    )
    clauses.append(
        f"(companies IS NOT NULL AND ({checks}))"
        if include
        else f"(companies IS NULL OR NOT ({checks}))"
    )


def append_document_clause(
    clauses: List[str],
    values: Optional[List[str]],
    include: bool
) -> None:
    """
    Append a document-hash membership clause.

    :param clauses: Mutable SQL clause collection.
    :param values: Document hashes.
    :param include: Whether values are included or excluded.
    :return: None.
    """
    if not values:
        return
    operator = "IN" if include else "NOT IN"
    literals = ", ".join(
        sql_literal(value=value)
        for value in values
    )
    clauses.append(f"doc {operator} ({literals})")


def sql_literal(
    value: str
) -> str:
    """
    Quote a SQL string literal.

    :param value: Unquoted text.
    :return: Safely quoted SQL literal.
    """
    return "'" + value.replace("'", "''") + "'"
