from dataclasses import asdict, dataclass, field

from nosible.classes.snippet_set import SnippetSet
from nosible.utils.json_tools import json_dumps, json_loads


@dataclass(init=True, repr=True, eq=True, frozen=True)
class WebPageData:
    """
    A data container for all extracted and processed information about a web page.

    Parameters
    ----------
    full_text : str or None
        The full textual content of the web page, or None if not available.
    languages : dict
        A dictionary mapping language codes to their probabilities or counts, representing detected languages.
    metadata : dict
        Metadata extracted from the web page, such as description, keywords, author, etc.
    page : dict
        Page-specific details, such as title, canonical URL, and other page-level information.
    request : dict
        Information about the HTTP request and response, such as headers, status code, and timing.
    snippets : SnippetSet
        A set of extracted text snippets or highlights from the page, wrapped in a SnippetSet object.
    statistics : dict
        Statistical information about the page, such as word count, sentence count, or other computed metrics.
    structured : list
        A list of structured data objects (e.g., schema.org, OpenGraph) extracted from the page.
    url_tree : dict
        A hierarchical representation of the URL structure, such as breadcrumbs or navigation paths.

    Examples
    --------
    >>> data = WebPageData(languages={"en": 1}, metadata={"description": "Example"})
    >>> data.languages
    {'en': 1}
    >>> data.metadata
    {'description': 'Example'}
    """

    companies: list = None
    """A list of companies mentioned in the webpage, if applicable. (GKIDS)"""
    full_text: str = None
    """The full text content of the webpage."""
    languages: dict = None
    """Detected languages and their probabilities or counts."""
    metadata: dict = None
    """Metadata extracted from the webpage (e.g., description, keywords)."""
    page: dict = None
    """Page-specific details such as title, canonical URL, etc."""
    request: dict = None
    """Information about the HTTP request/response."""
    snippets: SnippetSet = field(init=True, default_factory=SnippetSet)
    """Extracted text snippets or highlights from the page."""
    statistics: dict = None
    """Statistical information about the page (e.g., word count)."""
    structured: list = None
    """Structured data (e.g., schema.org, OpenGraph)."""
    url_tree: dict = None
    """Hierarchical representation of the URL structure."""

    def __str__(self):
        """Return a string representation of the WebPageData.

        Returns
        -------
        str
            A string representation of the WebPageData instance, including languages, metadata, and other fields.
        """
        return (
            f"WebPageData(languages={self.languages}, metadata={self.metadata}, "
            f"page={self.page}, request={self.request}, snippets={self.snippets}, "
            f"statistics={self.statistics}, structured={self.structured}, url_tree={self.url_tree})"
        )

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
        data = asdict(self)
        # snippets is still a SnippetSet instance, so convert it:
        data["snippets"] = self.snippets.to_dict()
        return data

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
        >>> import json
        >>> d = json.loads(content)
        >>> d["languages"]
        {'en': 1}
        >>> d["metadata"]
        {'description': 'Example'}
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
        data_dict = json_loads(data)
        # Handle snippets separately to avoid passing it twice
        snippets_data = data_dict.pop("snippets", None)
        if snippets_data is not None:
            data_dict["snippets"] = SnippetSet.from_dict(snippets_data)
        return cls(**data_dict)

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
            data = json_loads(f.read())
        # Handle snippets separately to avoid passing it twice
        snippets_data = data.pop("snippets", None)
        if snippets_data is not None:
            data["snippets"] = SnippetSet.from_dict(snippets_data)
        return cls(**data)
