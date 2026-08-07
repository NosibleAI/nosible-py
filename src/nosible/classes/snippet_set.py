"""Collection model for NOSIBLE snippets."""

import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Dict, List

from nosible.classes.snippet import Snippet
from nosible.utils.json_tools import json_dumps

MODULE_NAME = os.path.basename(p=__file__)


@dataclass
class SnippetSet(Iterator[Snippet]):
    """Mutable iterator and collection of snippets."""

    snippets: List[Snippet] = field(default_factory=list)
    index: int = field(
        default=0,
        init=False,
        repr=False,
        compare=False
    )

    def __iter__(
        self: "SnippetSet"
    ) -> "SnippetSet":
        """
        Reset iteration and return this collection.

        :return: Reset snippet iterator.
        """
        self.index = 0
        return self

    def __next__(
        self: "SnippetSet"
    ) -> Snippet:
        """
        Return the next snippet.

        :return: Next snippet in the collection.
        """
        if self.index < len(self.snippets):
            snippet = self.snippets[self.index]
            self.index += 1
            return snippet
        raise StopIteration

    def __len__(
        self: "SnippetSet"
    ) -> int:
        """
        Return the number of snippets.

        :return: Number of snippets in the collection.
        """
        return len(self.snippets)

    def __getitem__(
        self: "SnippetSet",
        index: int
    ) -> Snippet:
        """
        Return a snippet by index.

        :param index: Snippet index.
        :return: Snippet at the requested index.
        """
        try:
            return self.snippets[index]
        except IndexError as error:
            raise IndexError(
                f"{MODULE_NAME}: index {index} out of range for "
                f"{len(self.snippets)} snippets"
            ) from error

    def __str__(
        self: "SnippetSet"
    ) -> str:
        """
        Return all snippets as text.

        :return: Newline-delimited snippet representations.
        """
        return "\n".join(
            str(snippet)
            for snippet in self.snippets
        )

    def write_json(
        self: "SnippetSet"
    ) -> str:
        """
        Convert the collection to JSON.

        :return: JSON representation of the snippets.
        """
        return json_dumps(obj=self.to_dict())

    def to_dict(
        self: "SnippetSet"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Convert snippets to a hash-keyed dictionary.

        :return: Dictionary of snippet payloads.
        """
        return {
            snippet.snippet_hash: snippet.to_dict()
            for snippet in self.snippets
        }

    @classmethod
    def from_dict(
        cls: "type[SnippetSet]",
        data: Dict[str, Dict[str, Any]]
    ) -> "SnippetSet":
        """
        Create a snippet set from a hash-keyed dictionary.

        :param data: Snippet payloads keyed by snippet hash.
        :return: Parsed snippet set.
        """
        if not isinstance(data, dict):
            raise ValueError(
                f"{MODULE_NAME}: SnippetSet data must be a dictionary"
            )
        return cls(
            snippets=[
                Snippet.from_dict(data=snippet)
                for snippet in data.values()
            ]
        )
