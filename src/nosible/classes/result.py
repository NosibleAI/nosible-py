"""Model for individual NOSIBLE Search results."""

import os
import copy
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from openai import OpenAI

import nosible.classes.result_set
import nosible.classes.search
from nosible.classes.web_page import WebPageData
from nosible.utils.json_tools import print_dict

MODULE_NAME = os.path.basename(p=__file__)
RESULT_FIELDS: Set[str] = {
    "url",
    "title",
    "description",
    "netloc",
    "published",
    "visited",
    "author",
    "content",
    "best_chunk",
    "language",
    "similarity",
    "url_hash",
    "brand_safety",
    "continent",
    "region",
    "country",
    "sector",
    "industry_group",
    "industry",
    "sub_industry",
    "iab_tier_1",
    "iab_tier_2",
    "iab_tier_3",
    "iab_tier_4",
    "semantics"
}


@dataclass
class Result:
    """One losslessly represented Search result."""

    url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    netloc: Optional[str] = None
    published: Optional[str] = None
    visited: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None
    best_chunk: Optional[str] = None
    language: Optional[str] = None
    similarity: Optional[float] = None
    url_hash: Optional[str] = None
    brand_safety: Optional[str] = None
    continent: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    industry_group: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    iab_tier_1: Optional[str] = None
    iab_tier_2: Optional[str] = None
    iab_tier_3: Optional[str] = None
    iab_tier_4: Optional[str] = None
    semantics: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = field(
        default_factory=dict,
        repr=False
    )
    present_fields: Set[str] = field(
        default_factory=set,
        init=False,
        repr=False,
        compare=False
    )

    def __str__(
        self: "Result"
    ) -> str:
        """
        Return populated result fields as readable JSON.

        :return: Formatted result fields.
        """
        populated_fields = {
            key: value
            for key, value in self.to_dict().items()
            if value is not None
        }
        return print_dict(data=populated_fields)

    def __getitem__(
        self: "Result",
        key: str
    ) -> Any:
        """
        Return a result field by name.

        :param key: Result field name.
        :return: Selected result value.
        """
        try:
            return object.__getattribute__(self, key)
        except AttributeError as error:
            raise KeyError(f"Key '{key}' not found in Result") from error

    def __add__(
        self: "Result",
        other: "Result"
    ) -> "nosible.classes.result_set.ResultSet":
        """
        Combine two results into a result set.

        :param other: Result to add.
        :return: Result set containing both results.
        """
        if not isinstance(other, Result):
            raise TypeError("Can only add another Result instance")
        return nosible.classes.result_set.ResultSet(
            results=[
                self,
                other
            ]
        )

    def scrape_url(
        self: "Result",
        client: Any
    ) -> WebPageData:
        """
        Scrape the URL associated with this result.

        :param client: Configured NOSIBLE client.
        :return: Scraped web-page data.
        """
        if not self.url:
            raise ValueError("Cannot scrape Result without a URL")
        return client.scrape_url(url=self.url)

    def sentiment(
        self: "Result",
        client: Any
    ) -> float:
        """
        Score this result's content with the configured LLM.

        :param client: Configured NOSIBLE client with an LLM API key.
        :return: Sentiment score from negative one to positive one.
        """
        if client is None:
            raise ValueError(
                "A Nosible client instance must be provided as 'client'"
            )
        if not client.llm_api_key:
            raise ValueError(
                "LLM API key is required for getting result sentiment"
            )

        content = self.content or ""
        prompt = (
            "On a scale from -1.0 (very negative) to 1.0 (very positive), "
            "rate the sentiment of the following text and return only the "
            f"numeric score:\n{content.strip()}"
        )
        llm_client = OpenAI(
            base_url=client.openai_base_url,
            api_key=client.llm_api_key
        )
        response = llm_client.chat.completions.create(
            model=client.sentiment_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )
        raw_score = response.choices[0].message.content
        try:
            score = float(raw_score)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Sentiment response is not a float: {raw_score!r}"
            ) from error
        if not -1.0 <= score <= 1.0:
            raise ValueError(
                f"Sentiment {score} outside valid range [-1.0, 1.0]"
            )
        return score

    def similar(
        self: "Result",
        client: Any,
        sql_filter: Optional[str] = None,
        n_results: int = 100,
        n_probes: int = 30,
        n_contextify: int = 128,
        algorithm: str = "hybrid-3",
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
        *args: Any,
        **kwargs: Any
    ) -> "nosible.classes.result_set.ResultSet":
        """
        Find results similar to this result while excluding the source document.

        :param client: Configured NOSIBLE client.
        :param sql_filter: Optional SQL filter.
        :param n_results: Maximum result count.
        :param n_probes: Number of search probes.
        :param n_contextify: Context size per result.
        :param algorithm: Retrieval algorithm.
        :param publish_start: Earliest publication date.
        :param publish_end: Latest publication date.
        :param visited_start: Earliest NOSIBLE visit date.
        :param visited_end: Latest NOSIBLE visit date.
        :param certain: Whether dates must be certain.
        :param include_netlocs: Domains to include.
        :param exclude_netlocs: Domains to exclude.
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
        :param instruction: Additional retrieval instruction.
        :param args: Ignored legacy positional arguments.
        :param kwargs: Deprecated legacy keyword arguments.
        :return: Similar search results.
        """
        if args:
            warnings.warn(
                message="Additional positional arguments are ignored",
                category=DeprecationWarning,
                stacklevel=2
            )
        if "include_languages" in kwargs or "exclude_languages" in kwargs:
            warnings.warn(
                message=(
                    "Language list filters are deprecated; use 'language' instead"
                ),
                category=DeprecationWarning,
                stacklevel=2
            )
        if client is None:
            raise ValueError(
                "A Nosible client instance must be provided as 'client'"
            )
        if not self.url:
            raise ValueError("Cannot find similar results without a URL")

        excluded_documents = list(exclude_docs) if exclude_docs else []
        if self.url_hash and self.url_hash not in excluded_documents:
            excluded_documents.append(self.url_hash)
        search = nosible.classes.search.Search(
            question=self.title,
            expansions=[],
            sql_filter=sql_filter,
            n_results=n_results,
            n_probes=n_probes,
            n_contextify=n_contextify,
            algorithm=algorithm,
            publish_start=publish_start,
            publish_end=publish_end,
            visited_start=visited_start,
            visited_end=visited_end,
            certain=certain,
            include_netlocs=include_netlocs,
            exclude_netlocs=exclude_netlocs,
            include_companies=include_companies,
            exclude_companies=exclude_companies,
            include_docs=include_docs,
            exclude_docs=excluded_documents,
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
            instruction=instruction
        )
        return client.fast_search(search=search)

    def to_dict(
        self: "Result"
    ) -> Dict[str, Any]:
        """
        Convert the result to its lossless dictionary representation.

        :return: Search result payload.
        """
        selected_fields = (
            self.present_fields & RESULT_FIELDS
            if self.present_fields
            else RESULT_FIELDS
        )
        data = {
            name: copy.deepcopy(x=getattr(self, name))
            for name in RESULT_FIELDS
            if name in selected_fields
            and not (
                name == "semantics"
                and self.semantics is None
                and not self.present_fields
            )
        }
        data.update(copy.deepcopy(x=self.extra))
        return data

    @classmethod
    def from_dict(
        cls: "type[Result]",
        data: Dict[str, Any]
    ) -> "Result":
        """
        Create a result without discarding unknown response fields.

        :param data: Search result payload.
        :return: Parsed result.
        """
        if not isinstance(data, dict):
            raise ValueError(
                f"{MODULE_NAME}: Result data must be a dictionary"
            )

        semantics = copy.deepcopy(x=data.get("semantics"))
        similarity = copy.deepcopy(x=data.get("similarity"))
        if "similarity" not in data and isinstance(semantics, dict):
            similarity = semantics.get("similarity")
        best_chunk = copy.deepcopy(x=data.get("best_chunk"))
        if "best_chunk" not in data and isinstance(semantics, dict):
            best_chunk = semantics.get("best_chunk")

        values = {
            key: copy.deepcopy(x=value)
            for key, value in data.items()
            if key in RESULT_FIELDS
            and key not in {
                "similarity",
                "best_chunk"
            }
        }
        values["similarity"] = similarity
        values["best_chunk"] = best_chunk
        values["extra"] = {
            key: copy.deepcopy(x=value)
            for key, value in data.items()
            if key not in RESULT_FIELDS
        }
        result = cls(**values)
        result.present_fields = set(data)
        return result
