"""Search request model for the NOSIBLE Search API."""

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

import nosible.classes.search_set
from nosible.utils.json_tools import json_dumps, json_loads, print_dict

SEARCH_FIELDS: Tuple[str, ...] = (
    "question",
    "expansions",
    "sql_filter",
    "n_results",
    "n_probes",
    "n_contextify",
    "algorithm",
    "min_similarity",
    "must_include",
    "must_exclude",
    "autogenerate_expansions",
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
    "exclude_docs",
    "brand_safety",
    "language",
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
    "instruction",
    "companies",
    "collection",
    "deduplicate",
    "internal_use"
)


@dataclass
class Search:
    """Parameters for a NOSIBLE Search request."""

    question: Optional[str] = None
    expansions: Optional[List[str]] = None
    sql_filter: Optional[str] = None
    n_results: Optional[int] = None
    n_probes: Optional[int] = None
    n_contextify: Optional[int] = None
    algorithm: Optional[str] = None
    min_similarity: Optional[float] = None
    must_include: Optional[List[str]] = None
    must_exclude: Optional[List[str]] = None
    autogenerate_expansions: bool = False
    publish_start: Optional[str] = None
    publish_end: Optional[str] = None
    visited_start: Optional[str] = None
    visited_end: Optional[str] = None
    certain: Optional[bool] = None
    include_netlocs: Optional[List[str]] = None
    exclude_netlocs: Optional[List[str]] = None
    include_companies: Optional[List[str]] = None
    exclude_companies: Optional[List[str]] = None
    include_docs: Optional[List[str]] = None
    exclude_docs: Optional[List[str]] = None
    brand_safety: Optional[str] = None
    language: Optional[str] = None
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
    instruction: Optional[str] = None
    companies: Optional[List[str]] = None
    collection: Optional[str] = None
    deduplicate: Optional[bool] = None
    internal_use: Optional[Dict[str, Any]] = None

    def __str__(
        self: "Search"
    ) -> str:
        """
        Return a readable representation of populated search fields.

        :return: Formatted search parameters.
        """
        return print_dict(data=self.to_dict())

    def __add__(
        self: "Search",
        other: "Search"
    ) -> "nosible.classes.search_set.SearchSet":
        """
        Combine two searches into a search set.

        :param other: Search to add.
        :return: Search set containing both searches.
        """
        if not isinstance(other, Search):
            raise TypeError("Can only add another Search instance")
        return nosible.classes.search_set.SearchSet(
            searches_list=[
                self,
                other
            ]
        )

    def write_json(
        self: "Search",
        path: str
    ) -> None:
        """
        Write the search to a JSON file.

        :param path: Destination file path.
        :return: None.
        """
        file_path = os.fspath(path=path)
        with open(
            file=file_path,
            mode="w",
            encoding="utf-8"
        ) as file_handle:
            file_handle.write(json_dumps(obj=self.to_dict()))

    def to_dict(
        self: "Search"
    ) -> Dict[str, Any]:
        """
        Convert the search to a dictionary.

        :return: Search parameters.
        """
        return asdict(
            obj=self,
            dict_factory=dict
        )

    @classmethod
    def read_json(
        cls: "type[Search]",
        path: str
    ) -> "Search":
        """
        Read a search from a JSON file.

        :param path: Source file path.
        :return: Parsed search.
        """
        file_path = os.fspath(path=path)
        with open(
            file=file_path,
            encoding="utf-8"
        ) as file_handle:
            data = json_loads(value=file_handle.read())
        return cls.from_dict(data=data)

    @classmethod
    def from_dict(
        cls: "type[Search]",
        data: Dict[str, Any]
    ) -> "Search":
        """
        Create a search from known dictionary fields.

        :param data: Search parameters.
        :return: Parsed search.
        """
        if not isinstance(data, dict):
            raise ValueError("Search data must be a dictionary")
        return cls(
            **{
                field_name: data.get(field_name)
                for field_name in SEARCH_FIELDS
            }
        )
