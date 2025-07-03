from nosible.classes.snippet_set import SnippetSet
from nosible.utils.json_tools import json_dumps, json_loads


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

    def __init__(
        self,
        *,
        companies: list = None,
        full_text: str = None,
        languages: dict = None,
        metadata: dict = None,
        page: dict = None,
        request: dict = None,
        snippets: dict = None,
        statistics: dict = None,
        structured: list = None,
        url_tree: dict = None,
    ):
        """
        Initialize a WebPageData instance.

        Parameters
        ----------
        companies : list, optional
            A list of companies mentioned in the webpage, if applicable. (GKIDS)
        full_text : str, optional
            The full text content of the webpage.
        languages : dict, optional
            Detected languages and their probabilities or counts.
        metadata : dict, optional
            Metadata extracted from the webpage (e.g., description, keywords).
        page : dict, optional
            Page-specific details such as title, canonical URL, etc.
        request : dict, optional
            Information about the HTTP request/response.
        snippets : list, optional
            Extracted text snippets or highlights from the page.
        statistics : dict, optional
            Statistical information about the page (e.g., word count).
        structured : list, optional
            Structured data (e.g., schema.org, OpenGraph).
        url_tree : dict, optional
            Hierarchical representation of the URL structure.

        Examples
        --------
        >>> data = WebPageData(full_text="Example Domain", languages={"en": 1})
        >>> data.languages
        {'en': 1}
        """
        self.companies = companies or []
        if snippets is None:
            snippets = {}
        self.full_text = full_text
        self.languages = languages or {}
        self.metadata = metadata or {}
        self.page = page or {}
        self.request = request or {}
        self.snippets = SnippetSet(snippets)
        self.statistics = statistics or {}
        self.structured = structured or []
        self.url_tree = url_tree or {}

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

    def __repr__(self):
        """
        Return a JSON-formatted string representation of the WebPageData instance.

        Returns
        -------
        str
            JSON string representing the WebPageData for easy readability and debugging.

        Examples
        --------
        >>> data = WebPageData(languages={"en": 1}, metadata={"description": "Example"})
        >>> repr_str = repr(data)
        >>> isinstance(repr_str, str)
        True
        """
        return json_dumps(self.to_dict())

    def __getattr__(self, name):
        """
        Allow attribute access to the internal dictionaries.

        Raises
        ------
        AttributeError
            If the requested attribute does not exist in the WebPageData.

        Returns
        -------
        Any
            The value of the specified attribute if it exists, otherwise raises AttributeError.
        """
        try:
            return getattr(self, name)
        except AttributeError as e:
            # chain the new AttributeError onto the original one
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") from e

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
            "companies": self.companies,
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
        parsed_data = json_loads(data)
        return cls(
            companies=parsed_data.get("companies", []),
            full_text=parsed_data.get("full_text"),
            languages=parsed_data.get("languages"),
            metadata=parsed_data.get("metadata"),
            page=parsed_data.get("page"),
            request=parsed_data.get("request"),
            snippets=parsed_data.get("snippets", {}),
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
