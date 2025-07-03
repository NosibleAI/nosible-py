from typing import Iterator

from nosible.classes.snippet import Snippet
from nosible.utils.json_tools import json_dumps


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
    ...     "hash1": {"content": "Example snippet", "snippet_hash": "hash1"}
    ... }
    >>> snippets = SnippetSet(snippets_data)
    >>> for snippet in snippets:
    ...     print(snippet.content)
    Example snippet
    """

    def __init__(self, snippets: dict) -> None:
        self._snippets = []

        for key, value in snippets.items():
            self._snippets.append(
                Snippet(
                    companies=value.get("companies", []),
                    content=value.get("content", ""),
                    images=value.get("images", []),
                    language=value.get("language", ""),
                    next_snippet_hash=value.get("next_snippet_hash", ""),
                    prev_snippet_hash=value.get("prev_snippet_hash", ""),
                    snippet_hash=key,
                    statistics=value.get("statistics", {}),
                    url_hash=value.get("url_hash", ""),
                    words=value.get("words", ""),
                )
            )

        self._index = 0

    def __iter__(self):
        """
        Initialize the iterator.
        Returns
        -------
        SnippetSet
            The iterator itself.
        """
        self._index = 0
        return self

    def __next__(self) -> Snippet:
        """
        Returns the next Snippet object from the collection.

        Returns
        -------
        Snippet
            The next snippet in the sequence.

        Raises
        ------
        StopIteration
            If there are no more snippets to return.
        """
        if self._index < len(self._snippets):
            snippet = self._snippets[self._index]
            self._index += 1
            return snippet
        raise StopIteration

    def __len__(self) -> int:
        """
        Returns the number of snippets in the collection.

        Returns
        -------
        int
            The number of snippets.
        """
        return len(self._snippets)

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
        if index < 0 or index >= len(self._snippets):
            raise IndexError("Index out of range.")
        return self._snippets[index]

    def __str__(self):
        """
        Print the content of all snippets in the set.
        Returns
        -------
        str
        """
        return "\n".join(str(s) for s in self)

    def __repr__(self):
        """
        Returns a string representation of the SnippetSet object.

        Returns
        -------
        str
            A string representation of the SnippetSet.
        """
        return f"SnippetSet(snippets={len(self._snippets)})"

    def to_dict(self) -> dict:
        """
        Convert the SnippetSet to a dictionary representation.

        Returns
        -------
        dict
            Dictionary containing all snippets indexed by their hash.

        Examples
        --------
        >>> snippets_data = {
        ...     "hash1": {"content": "Example snippet", "snippet_hash": "hash1"}
        ... }
        >>> snippets = SnippetSet(snippets_data)
        >>> snippets_dict = snippets.to_dict()
        >>> isinstance(snippets_dict, dict)
        True
        """
        return {s.snippet_hash: s.to_dict() for s in self._snippets} if self._snippets else {}

    def to_json(self) -> str:
        """
        Convert the SnippetSet to a JSON string representation.

        Returns
        -------
        str
            JSON string containing all snippets indexed by their hash.

        Examples
        --------
        >>> snippets_data = {
        ...     "hash1": {"content": "Example snippet", "snippet_hash": "hash1"}
        ... }
        >>> snippets = SnippetSet(snippets_data)
        >>> json_str = snippets.to_json()
        >>> isinstance(json_str, str)
        True
        """
        return json_dumps(self.to_dict())
