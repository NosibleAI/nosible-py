"""Model for web pages returned by the scrape endpoint."""

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from nosible.classes.snippet_set import SnippetSet
from nosible.utils.json_tools import json_dumps, json_loads


@dataclass(
    init=True,
    repr=True,
    eq=True,
    frozen=True
)
class WebPageData:
    """Extracted and processed data for one web page."""

    full_text: Optional[str] = None
    languages: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    page: Optional[Dict[str, Any]] = None
    request: Optional[Dict[str, Any]] = None
    snippets: SnippetSet = field(default_factory=SnippetSet)
    statistics: Optional[Dict[str, Any]] = None
    structured: Optional[List[Any]] = None
    url_tree: Optional[Dict[str, Any]] = None

    def __str__(
        self: "WebPageData"
    ) -> str:
        """
        Return a concise representation of the web-page data.

        :return: Web-page data summary.
        """
        return (
            f"WebPageData(languages={self.languages}, metadata={self.metadata}, "
            f"page={self.page}, request={self.request}, "
            f"snippets={self.snippets}, statistics={self.statistics}, "
            f"structured={self.structured}, url_tree={self.url_tree})"
        )

    def write_json(
        self: "WebPageData",
        path: Optional[Union[Path, str]] = None
    ) -> str:
        """
        Serialize the web-page data and optionally write it to disk.

        :param path: Optional destination file path.
        :return: JSON representation of the web-page data.
        """
        json_text = json_dumps(obj=self.to_dict())
        if path is not None:
            file_path = os.fspath(path=path)
            with open(
                file=file_path,
                mode="w",
                encoding="utf-8"
            ) as file_handle:
                file_handle.write(json_text)
        return json_text

    def to_dict(
        self: "WebPageData"
    ) -> Dict[str, Any]:
        """
        Convert the web-page data to a dictionary.

        :return: Web-page payload.
        """
        data = asdict(obj=self)
        data["snippets"] = self.snippets.to_dict()
        return data

    @classmethod
    def read_json(
        cls: "type[WebPageData]",
        path: Union[Path, str]
    ) -> "WebPageData":
        """
        Read web-page data from a JSON file.

        :param path: Source file path.
        :return: Parsed web-page data.
        """
        file_path = os.fspath(path=path)
        with open(
            file=file_path,
            encoding="utf-8"
        ) as file_handle:
            data = json_loads(value=file_handle.read())
        if not isinstance(data, dict):
            raise ValueError("WebPageData JSON must contain an object")

        snippets_data = data.pop("snippets", None)
        if snippets_data is not None:
            data["snippets"] = SnippetSet.from_dict(data=snippets_data)
        return cls(**data)
