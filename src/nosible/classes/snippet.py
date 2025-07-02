from nosible.utils.json_tools import json_dumps


class Snippet:
    """
    A class representing a snippet of text, typically extracted from a web page.

    Attributes
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

    Methods
    -------
    to_dict()
        Convert the Snippet to a dictionary representation.
    to_json()
        Convert the Snippet to a JSON string representation.
    """

    def __init__(
        self,
        content: str = None,
        images: list = None,
        language: str = None,
        next_snippet_hash: str = None,
        prev_snippet_hash: str = None,
        snippet_hash: str = None,
        statistics: dict = None,
        url_hash: str = None,
        words: str = None,
    ):
        """
        Initialize a Snippet instance.

        Parameters
        ----------
        content : str
            The text content of the snippet.
        images : list, optional
            List of image URLs associated with the snippet.
        language : str, optional
            The language of the snippet.
        snippet_hash : str, optional
            A unique hash for the snippet.
        statistics : dict, optional
            Statistical information about the snippet (e.g., word count).
        words : str, optional
            The words in the snippet.

        Examples
        --------
        >>> snippet = Snippet(content="Example snippet", language="en")
        >>> print(snippet.content)
        Example snippet
        """
        self.content = content
        self.images = images
        self.language = language
        self.snippet_hash = snippet_hash
        self.statistics = statistics
        self.words = words
        self.url_hash = url_hash
        self.next_snippet_hash = next_snippet_hash
        self.prev_snippet_hash = prev_snippet_hash

    def __repr__(self):
        """
        Returns a string representation of the Snippet object.

        Returns
        -------
        str
            A string representation of the Snippet.
        """
        return f"Snippet(content={self.content[:30]}, language={self.language}, snippet_hash={self.snippet_hash})"

    def __str__(self):
        """
        Returns a user-friendly string representation of the Snippet.

        Returns
        -------
        str
            A string representation of the Snippet.
        """
        return f"Snippet: {self.content}"

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
        return {
            "content": self.content,
            "images": self.images,
            "language": self.language,
            "snippet_hash": self.snippet_hash,
            "statistics": self.statistics,
            "words": self.words,
            "url_hash": self.url_hash,
            "next_snippet_hash": self.next_snippet_hash,
            "prev_snippet_hash": self.prev_snippet_hash,
        }

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
