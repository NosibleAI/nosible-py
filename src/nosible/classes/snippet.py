"""Models for snippets returned by NOSIBLE Search."""

import os
import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from nosible.utils.json_tools import json_dumps, print_dict

MODULE_NAME = os.path.basename(p=__file__)
SNIPPET_FIELDS: Tuple[str, ...] = (
    "content",
    "images",
    "language",
    "next_snippet_hash",
    "prev_snippet_hash",
    "snippet_hash",
    "statistics",
    "url_hash",
    "words",
    "links",
    "videos",
    "audio",
    "files",
    "tables",
    "lists",
    "blocks"
)


@dataclass(
    init=True,
    repr=True,
    eq=True,
    frozen=True
)
class Snippet:
    """A lossless snippet returned by NOSIBLE Search."""

    content: Optional[str] = field(
        default=None,
        repr=True,
        compare=True
    )
    images: Optional[List[Any]] = field(
        default=None,
        repr=True,
        compare=False
    )
    language: Optional[str] = field(
        default=None,
        repr=True,
        compare=False
    )
    next_snippet_hash: Optional[str] = field(
        default=None,
        repr=True,
        compare=False
    )
    prev_snippet_hash: Optional[str] = field(
        default=None,
        repr=True,
        compare=False
    )
    snippet_hash: Optional[str] = field(
        default=None,
        repr=True,
        compare=True
    )
    statistics: Optional[Dict[str, Any]] = field(
        default=None,
        repr=False,
        compare=False
    )
    url_hash: Optional[str] = field(
        default=None,
        repr=True,
        compare=False
    )
    words: Optional[str] = field(
        default=None,
        repr=False,
        compare=False
    )
    links: Optional[List[Any]] = field(
        default=None,
        repr=False,
        compare=False
    )
    videos: Optional[List[Any]] = field(
        default=None,
        repr=False,
        compare=False
    )
    audio: Optional[List[Any]] = field(
        default=None,
        repr=False,
        compare=False
    )
    files: Optional[List[Any]] = field(
        default=None,
        repr=False,
        compare=False
    )
    tables: Optional[List[Any]] = field(
        default=None,
        repr=False,
        compare=False
    )
    lists: Optional[List[Any]] = field(
        default=None,
        repr=False,
        compare=False
    )
    blocks: Optional[List[Any]] = field(
        default=None,
        repr=False,
        compare=False
    )
    unknown_fields: Dict[str, Any] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False
    )
    present_fields: Optional[Set[str]] = field(
        default=None,
        init=False,
        repr=False,
        compare=False
    )

    def __str__(
        self: "Snippet"
    ) -> str:
        """
        Return a user-friendly string representation of the snippet.

        :return: Formatted snippet fields.
        """
        return print_dict(data=self.to_dict())

    def __getitem__(
        self: "Snippet",
        key: str
    ) -> Any:
        """
        Access a snippet attribute using dictionary-like syntax.

        :param key: Attribute name to access.
        :return: Value of the selected attribute.
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"'{key}' is not a valid Snippet attribute.")

    @classmethod
    def from_dict(
        cls: "type[Snippet]",
        data: Dict[str, Any]
    ) -> "Snippet":
        """
        Create a snippet without discarding unknown response fields.

        :param data: Snippet payload.
        :return: Parsed snippet.
        """
        if not isinstance(data, dict):
            raise ValueError(
                f"{MODULE_NAME}: Snippet data must be a dictionary"
            )

        snippet = cls(
            **{
                key: copy.deepcopy(x=value)
                for key, value in data.items()
                if key in SNIPPET_FIELDS
            }
        )
        object.__setattr__(
            snippet,
            "unknown_fields",
            {
                key: copy.deepcopy(x=value)
                for key, value in data.items()
                if key not in SNIPPET_FIELDS
            }
        )
        object.__setattr__(
            snippet,
            "present_fields",
            {
                key
                for key in data
                if key in SNIPPET_FIELDS
            }
        )
        return snippet

    def write_json(
        self: "Snippet"
    ) -> str:
        """
        Convert the snippet to JSON.

        :return: JSON representation of the snippet.
        """
        return json_dumps(data=self.to_dict())

    def to_dict(
        self: "Snippet"
    ) -> Dict[str, Any]:
        """
        Convert the snippet to a lossless dictionary representation.

        :return: Snippet payload.
        """
        selected_fields = (
            set(SNIPPET_FIELDS)
            if self.present_fields is None
            else self.present_fields
        )
        data = {
            name: copy.deepcopy(x=getattr(self, name))
            for name in SNIPPET_FIELDS
            if name in selected_fields
        }
        data.update(copy.deepcopy(x=self.unknown_fields))
        return data
