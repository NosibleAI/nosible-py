from nosible.utils.json_tools import json_dumps


class Snippet:
    """
    Represents a snippet of text extracted from a web page.

    Attributes
    ----------
    content : str, optional
    url_hash : str, optional
        Hash of the URL from which the snippet was extracted.
    next_snippet_hash : str, optional
        Hash of the next snippet in sequence.
    prev_snippet_hash : str, optional
        Hash of the previous snippet in sequence.

    Methods
    -------
    to_dict()
    to_json()"""

    """Represents a snippet of text extracted from a web page."""

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
