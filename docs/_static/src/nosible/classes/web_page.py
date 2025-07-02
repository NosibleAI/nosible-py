from nosible.classes.snippet_set import SnippetSet
from nosible.utils.json_tools import json_dumps, json_loads


class WebPageData:
    """
    Container class for storing and accessing parsed webpage information.

    This class encapsulates various aspects of a parsed webpage, including metadata, language detection,
    page details, request information, extracted snippets, statistics, structured data, and URL hierarchy.
    It provides convenient access to these components and supports conversion to dictionary and JSON formats.

    Examples
    --------
    >>> data = WebPageData(languages={"en": 1}, metadata={"description": "Example"})
    >>> data.languages
    {'en': 1}
    >>> data.metadata
    {'description': 'Example'}
    """

    def to_dict(self) -> dict:
        """
        Convert the WebPageData instance to a dictionary.

        Returns
        -------
        dict
            A dictionary containing all fields of the WebPageData.

        Examples
        --------
        >>> data = WebPageData(full_text="Example", languages={"en": 1}, metadata={"description": "Example"})
        >>> d = data.to_dict()
        >>> isinstance(d, dict)
        True
        >>> d["languages"] == {"en": 1}
        True
        """
        return {
            "full_text": self.full_text,
            "languages": self.languages,
            "metadata": self.metadata,
            "page": self.page,
            "request": self.request,
            "snippets": self.snippets.to_dict(),
            "statistics": self.statistics,
            "structured": self.structured,
            "url_tree": self.url_tree,
        }

    def to_json(self) -> str:
        """
        Convert the WebPageData to a JSON string representation.

        Returns
        -------
        str
            JSON string containing all fields of the WebPageData.

        Examples
        --------
        >>> data = WebPageData(languages={"en": 1}, metadata={"description": "Example"})
        >>> json_str = data.to_json()
        >>> isinstance(json_str, str)
        True
        >>> print(json_str)  # doctest: +ELLIPSIS
        {"full_text":null,"languages":{"en":1},"metadata":{"description":"Example"},...}
        """
        return json_dumps(self.to_dict())

    def save(self, path: str) -> None:
        """
        Save the WebPageData to a JSON file.

        Parameters
        ----------
        path : str
            Path to the file where the WebPageData will be saved.

        Examples
        --------
        >>> data = WebPageData(languages={"en": 1}, metadata={"description": "Example"})
        >>> data.save("test_webpage.json")
        >>> with open("test_webpage.json", "r", encoding="utf-8") as f:
        ...     content = f.read()
        >>> print(content)  # doctest: +ELLIPSIS
        {"full_text":null,"languages":{"en":1},"metadata":{"description":"Example"},...}
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def from_json(cls, data: str) -> "WebPageData":
        """
        Create a WebPageData instance from a JSON string.

        Parameters
        ----------
        data : str
            JSON string containing fields to initialize the WebPageData.

        Returns
        -------
        WebPageData
            An instance of WebPageData initialized with the provided JSON data.

        Examples
        --------
        >>> json_str = '{"languages": {"en": 1}, "metadata": {"description": "Example"}}'
        >>> webpage_data = WebPageData.from_json(json_str)
        >>> isinstance(webpage_data, WebPageData)
        True
        >>> webpage_data.languages
        {'en': 1}
        """
        parsed_data = json_loads(data)
        return cls(
            full_text=parsed_data.get("full_text"),
            languages=parsed_data.get("languages"),
            metadata=parsed_data.get("metadata"),
            page=parsed_data.get("page"),
            request=parsed_data.get("request"),
            snippets=parsed_data.get("snippets", []),
            statistics=parsed_data.get("statistics"),
            structured=parsed_data.get("structured"),
            url_tree=parsed_data.get("url_tree"),
        )

    @classmethod
    def load(cls, path: str) -> "WebPageData":
        """
        Create a WebPageData instance from a JSON file.

        Parameters
        ----------
        path : str
            Path to the JSON file containing fields to initialize the WebPageData.

        Returns
        -------
        WebPageData
            An instance of WebPageData initialized with the provided data.

        Examples
        --------
        >>> data = WebPageData(languages={"en": 1}, metadata={"description": "Example"})
        >>> data.save("test_webpage.json")
        >>> loaded = WebPageData.load("test_webpage.json")
        >>> isinstance(loaded, WebPageData)
        True
        >>> loaded.languages
        {'en': 1}
        """
        with open(path, encoding="utf-8") as f:
            data = f.read()
        return cls.from_json(data)
