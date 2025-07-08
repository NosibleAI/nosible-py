from dataclasses import asdict, dataclass, field

from nosible.utils.json_tools import json_dumps, print_dict


@dataclass(init=True, repr=True, eq=True, frozen=True)
class Snippet:
    """
    A class representing a snippet of text, typically extracted from a web page.

    Parameters
    ----------
    content : str or None
        The text content of the snippet.
    images : list or None
        List of image URLs associated with the snippet.
    language : str or None
        The language of the snippet.
    next_snippet_hash : str or None
        Hash of the next snippet in sequence.
    prev_snippet_hash : str or None
        Hash of the previous snippet in sequence.
    snippet_hash : str or None
        A unique hash for the snippet.
    statistics : dict or None
        Statistical information about the snippet.
    url_hash : str or None
        Hash of the URL from which the snippet was extracted.
    words : str or None
        The words in the snippet.
    links : list or None
        List of links associated with the snippet.
    companies : list or None
        List of companies mentioned in the snippet.


    Examples
    --------
    >>> snippet = Snippet(content="Example snippet", language="en")
    >>> print(snippet.content)
    Example snippet

    """

    content: str = field(default=None, repr=True, compare=True)
    """The text content of the snippet."""
    images: list = field(default=None, repr=True, compare=False)
    """List of image URLs associated with the snippet."""
    language: str = field(default=None, repr=True, compare=False)
    """The language of the snippet."""
    next_snippet_hash: str = field(default=None, repr=True, compare=False)
    """Hash of the next snippet in sequence."""
    prev_snippet_hash: str = field(default=None, repr=True, compare=False)
    """Hash of the previous snippet in sequence."""
    snippet_hash: str = field(default=None, repr=True, compare=True)
    """A unique hash for the snippet."""
    statistics: dict = field(default=None, repr=False, compare=False)
    """Statistical information about the snippet."""
    url_hash: str = field(default=None, repr=True, compare=False)
    """Hash of the URL from which the snippet was extracted."""
    words: str = field(default=None, repr=False, compare=False)
    """The words in the snippet."""
    links: list = field(default=None, repr=False, compare=False)
    """List of links associated with the snippet."""
    companies: list = field(default=None, repr=False, compare=False)
    """List of companies mentioned in the snippet."""

    def __str__(self):
        """
        Returns a user-friendly string representation of the Snippet.

        Returns
        -------
        str
            A string representation of the Snippet.
        """
        return print_dict(self.to_dict())

    def __getitem__(self, key: str):
        """
        Allows access to snippet attributes using dictionary-like syntax.

        Parameters
        ----------
        key : str
            The attribute name to access.

        Returns
        -------
        Any
            The value of the specified attribute.

        Raises
        ------
        KeyError
            If the key does not match any attribute.
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"'{key}' is not a valid Snippet attribute.")

    def to_dict(self) -> dict:
        """
        Convert the Snippet to a dictionary representation.

        Returns
        -------
        dict
            Dictionary containing all fields of the Snippet.

        Examples
        --------
        >>> snippet = Snippet(content="Example snippet", snippet_hash="hash1")
        >>> snippet_dict = snippet.to_dict()
        >>> isinstance(snippet_dict, dict)
        True
        """
        return asdict(self, dict_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Snippet":
        """
        Create a Snippet instance from a dictionary.

        Parameters
        ----------
        data : dict
            Dictionary containing snippet data.

        Returns
        -------
        Snippet
            An instance of Snippet populated with the provided data.

        Examples
        --------
        >>> snippet_data = {"content": "Example snippet", "snippet_hash": "hash1"}
        >>> snippet = Snippet.from_dict(snippet_data)
        >>> isinstance(snippet, Snippet)
        True
        """
        return cls(**data)

    def to_json(self) -> str:
        """
        Convert the Snippet to a JSON string representation.

        Returns
        -------
        str
            JSON string containing all fields of the Snippet.

        Examples
        --------
        >>> snippet = Snippet(content="Example snippet", snippet_hash="hash1")
        >>> json_str = snippet.to_json()
        >>> isinstance(json_str, str)
        True
        """
        return json_dumps(self.to_dict())
