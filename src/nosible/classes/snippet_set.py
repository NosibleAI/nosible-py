from typing import Iterator

from nosible.classes.snippet import Snippet
from nosible.utils.json_tools import json_dumps


class SnippetSet(Iterator[Snippet]):
    """
    An iterator and container for a collection of Snippet objects.
    This class allows iteration over, indexing into, and serialization of a set of Snippet objects.
    It supports initialization from a list of Snippet instances, dictionaries, or strings, and provides
    methods for converting the collection to dictionary and JSON representations.

    Attributes
    ----------
    _snippets : list of Snippet
        The internal list storing Snippet objects.
    _index : int
        The current index for iteration.

    Methods
    -------
    __init__(snippets)
        Initialize the SnippetSet with a list of Snippet objects, dictionaries, or strings.
    __iter__()
        Return the iterator object itself and reset the iteration index.
    __next__()
        Return the next Snippet object in the collection.
    __len__()
        Return the number of snippets in the collection.
    __getitem__(index)
        Return the Snippet at the specified index.
    to_dict()
        Convert the SnippetSet to a dictionary indexed by snippet hash.
    to_json()"""

    def __init__(self, snippets: list[Snippet]) -> None:
        """
        Initialize a SnippetSet iterator.

        Parameters
        ----------
        snippets : list
            A list of Snippet objects.

        Examples
        --------
        >>> snippets = SnippetSet([Snippet(content="Example snippet")])
        >>> for snippet in snippets:
        ...     print(snippet.content)
        Example snippet
        """
        self._snippets: list[Snippet] = [
            s if isinstance(s, Snippet) else Snippet(**s) if isinstance(s, dict) else Snippet(content=str(s))
            for s in snippets
        ]
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
        return self._snippets[index]

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
        >>> snippets = SnippetSet([Snippet(content="Example snippet", snippet_hash="hash1")])
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
        >>> snippets = SnippetSet([Snippet(content="Example snippet", snippet_hash="hash1")])
        >>> json_str = snippets.to_json()
        >>> isinstance(json_str, str)
        True
        """
        return json_dumps(self.to_dict())
