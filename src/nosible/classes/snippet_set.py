from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from nosible.classes.snippet import Snippet
from nosible.utils.json_tools import json_dumps


@dataclass()
class SnippetSet(Iterator[Snippet]):
    """
    An iterator and container for a collection of Snippet objects.
    This class allows iteration over, indexing into, and serialization of a set of Snippet objects.
    It supports initialization from a dictionary of snippet data, and provides
    methods for converting the collection to dictionary and JSON representations.

    Parameters
    ----------
    snippets : dict
        A dictionary where keys are snippet hashes and values are dictionaries of snippet attributes.

    Examples
    --------
    >>> snippets_data = {
    ...     "hash1": {"content": "Example snippet", "snippet_hash": "hash1"},
    ...     "hash2": {"content": "Another snippet", "snippet_hash": "hash2"},
    ... }
    >>> snippets = SnippetSet().from_dict(snippets_data)
    >>> for snippet in snippets:
    ...     print(snippet.content)
    Example snippet
    Another snippet
    """

    snippets: list[Snippet] = field(default_factory=list)
    """ List of `Snippet` objects contained in this ResultSet."""
    _index: int = field(default=0, init=False, repr=False, compare=False)
    """ Internal index for iteration over snippets."""

    def __iter__(self) -> SnippetSet:
        """
        Reset iteration and return self.

        Returns
        -------
        ResultSet
            Iterator over the ResultSet instance.
        """
        object.__setattr__(self, "_index", 0)
        return self

    def __next__(self) -> Snippet:
        """
        Returns the next Result in the sequence.

        Returns
        -------
        Result
            The next Result object in the sequence.
        Raises
        ------
        StopIteration
            If the end of the sequence is reached.
        """
        if self._index < len(self.snippets):
            item = self.snippets[self._index]
            object.__setattr__(self, "_index", self._index + 1)
            return item
        raise StopIteration

    def __len__(self) -> int:
        """
        Returns the number of snippets in the collection.

        Returns
        -------
        int
            The number of snippets.
        """
        return len(self.snippets)

    def __getitem__(self, index: int) -> Snippet:
        """
        Returns the Snippet at the specified index.

        Parameters
        ----------
        index : int
            The index of the snippet to retrieve.

        Returns
        -------
        Snippet
            The snippet at the specified index.

        Raises
        ------
        IndexError
            If the index is out of range.
        """
        if 0 <= index < len(self.snippets):
            return self.snippets[index]
        raise IndexError(f"Index {index} out of range for SnippetSet of length {len(self.snippets)}.")

    def __str__(self):
        """
        Print the content of all snippets in the set.
        Returns
        -------
        str
        """
        return "\n".join(str(s) for s in self)

    def to_dict(self) -> dict:
        """
        Convert the SnippetSet to a dictionary representation.

        Returns
        -------
        dict
            Dictionary containing all snippets indexed by their hash.

        Examples
        --------
        >>> snippets_data = {"hash1": {"content": "Example snippet", "snippet_hash": "hash1"}}
        >>> snippets = SnippetSet().from_dict(snippets_data)
        >>> snippets_dict = snippets.to_dict()
        >>> isinstance(snippets_dict, dict)
        True
        """
        return {s.snippet_hash: s.to_dict() for s in self.snippets} if self.snippets else {}

    def to_json(self) -> str:
        """
        Convert the SnippetSet to a JSON string representation.

        Returns
        -------
        str
            JSON string containing all snippets indexed by their hash.

        Examples
        --------
        >>> snippets_data = {"hash1": {"content": "Example snippet", "snippet_hash": "hash1"}}
        >>> snippets = SnippetSet().from_dict(snippets_data)
        >>> json_str = snippets.to_json()
        >>> isinstance(json_str, str)
        True
        """
        return json_dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> SnippetSet:
        """
        Create a SnippetSet instance from a dictionary.

        Parameters
        ----------
        data : dict
            Dictionary containing snippet data.

        Returns
        -------
        SnippetSet
            An instance of SnippetSet populated with the provided data.

        Examples
        --------
        >>> snippets_data = {"hash1": {"content": "Example snippet", "snippet_hash": "hash1"}}
        >>> snippets = SnippetSet.from_dict(snippets_data)
        >>> isinstance(snippets, SnippetSet)
        True
        """
        return cls([Snippet.from_dict(s) for s in data.values()])
