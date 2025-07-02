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
    -------.
    to_dict()
        Convert the SnippetSet to a dictionary indexed by snippet hash.
    to_json()"""

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
