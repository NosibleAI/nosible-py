"""Collection model for NOSIBLE searches."""

import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import nosible.classes.search
from nosible.utils.json_tools import json_dumps, json_loads


@dataclass
class SearchSet(Iterator[Any]):
    """Mutable iterator and collection of Search objects."""

    searches_list: List[Any] = field(default_factory=list)
    index: int = field(
        default=0,
        init=False,
        repr=False,
        compare=False
    )

    def __iter__(
        self: "SearchSet"
    ) -> "SearchSet":
        """
        Reset iteration and return this collection.

        :return: Reset search iterator.
        """
        self.index = 0
        return self

    def __next__(
        self: "SearchSet"
    ) -> Any:
        """
        Return the next search.

        :return: Next search in the collection.
        """
        if self.index < len(self.searches_list):
            search = self.searches_list[self.index]
            self.index += 1
            return search
        raise StopIteration

    def __str__(
        self: "SearchSet"
    ) -> str:
        """
        Return the indexed questions in the collection.

        :return: Newline-delimited search questions.
        """
        return "\n".join(
            f"{index}: {search.question}"
            for index, search in enumerate(self.searches_list)
        )

    def __getitem__(
        self: "SearchSet",
        index: int
    ) -> Any:
        """
        Return a search by index.

        :param index: Search index.
        :return: Search at the requested index.
        """
        try:
            return self.searches_list[index]
        except IndexError as error:
            raise IndexError(
                f"Index {index} out of range for {len(self.searches_list)} searches"
            ) from error

    def __len__(
        self: "SearchSet"
    ) -> int:
        """
        Return the number of searches.

        :return: Number of searches in the collection.
        """
        return len(self.searches_list)

    def __add__(
        self: "SearchSet",
        other: "SearchSet"
    ) -> "SearchSet":
        """
        Combine two search sets.

        :param other: Search set to add.
        :return: Combined search set.
        """
        if not isinstance(other, SearchSet):
            raise TypeError("Can only add another SearchSet instance")
        return SearchSet(
            searches_list=self.searches_list + other.searches_list
        )

    def __setitem__(
        self: "SearchSet",
        index: int,
        value: Any
    ) -> None:
        """
        Replace a search at an index.

        :param index: Search index.
        :param value: Replacement search.
        :return: None.
        """
        try:
            self.searches_list[index] = value
        except IndexError as error:
            raise IndexError(
                f"Index {index} out of range for {len(self.searches_list)} searches"
            ) from error

    def add(
        self: "SearchSet",
        search: Any
    ) -> None:
        """
        Add a search to the collection.

        :param search: Search to append.
        :return: None.
        """
        if not isinstance(search, nosible.classes.search.Search):
            raise TypeError("search must be a Search instance")
        self.searches_list.append(search)

    def remove(
        self: "SearchSet",
        index: int
    ) -> None:
        """
        Remove a search by index.

        :param index: Search index to remove.
        :return: None.
        """
        del self.searches_list[index]

    def write_json(
        self: "SearchSet",
        path: Optional[str] = None
    ) -> Optional[str]:
        """
        Serialize the collection and optionally write it to disk.

        :param path: Optional destination file path.
        :return: JSON string when no path is supplied, otherwise None.
        """
        json_text = json_dumps(obj=self.to_dicts())
        if path is None:
            return json_text

        file_path = os.fspath(path=path)
        with open(
            file=file_path,
            mode="w",
            encoding="utf-8"
        ) as file_handle:
            file_handle.write(json_text)
        return None

    def to_dicts(
        self: "SearchSet"
    ) -> List[Dict[str, Any]]:
        """
        Convert all searches to dictionaries.

        :return: Search parameter dictionaries.
        """
        return [
            search.to_dict()
            for search in self.searches_list
        ]

    @classmethod
    def read_json(
        cls: "type[SearchSet]",
        path: str
    ) -> "SearchSet":
        """
        Read a search collection from a JSON file.

        :param path: Source file path.
        :return: Parsed search set.
        """
        file_path = os.fspath(path=path)
        with open(
            file=file_path,
            encoding="utf-8"
        ) as file_handle:
            data = json_loads(value=file_handle.read())
        if not isinstance(data, list):
            raise ValueError("SearchSet JSON must contain a list")
        return cls(
            searches_list=[
                nosible.classes.search.Search.from_dict(data=item)
                for item in data
            ]
        )
