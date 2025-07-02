from __future__ import annotations

from typing import TYPE_CHECKING

from nosible.utils.json_tools import json_dumps, json_loads

if TYPE_CHECKING:
    from nosible.classes.search_set import SearchSet


class Search:
    """
    Represents the parameters for a search operation.

    This class encapsulates all configurable options for performing a search,
    such as the query text, filters, result limits, and algorithm selection.

    Attributes
    ----------
    question : str, optional
        The main search query.
    expansions : list of str, optional
        Additional query expansions.
    sql_filter : str, optional
        SQL filter to constrain results.
    n_results : int, optional
        Number of results to return.
    n_probes : int, optional
        Number of probes for the search algorithm.
    n_contextify : int, optional
        Number of context tokens to consider.
    algorithm : str, optional
        Search algorithm to use.
    output_type : str, optional
        Format of the output.
    publish_start : str, optional
        Start date for publish filtering (ISO format).
    publish_end : str, optional
        End date for publish filtering (ISO format).
    include_netlocs : list of str, optional
        Domains to include.
    exclude_netlocs : list of str, optional
        Domains to exclude.
    visited_start : str, optional
        Start date for visit filtering (ISO format).
    visited_end : str, optional
        End date for visit filtering (ISO format).
    certain : bool, optional
        If True, restrict to high-certainty results.
    include_languages : list of str, optional
        Languages to include.
    exclude_languages : list of str, optional
        Languages to exclude.
    include_companies : list of str, optional
        Companies to include.
    exclude_companies : list of str, optional
        Companies to exclude.
    include_docs : list of str, optional
        URL hash of docs to include.
    exclude_docs : list of str, optional
        URL hash of docs to exclude.

    Methods
    -------
    __init__(...)
        Initialize a Search instance with the given parameters.
    __str__()
        Return a readable string representation of the search parameters.
    __add__(other)
        Combine two Search instances into a SearchSet.
    to_dict()
        Convert the Search instance into a dictionary.
    from_dict(data)
        Construct a Search instance from a dictionary.
    save(path)
        Save the current Search instance to a JSON file.
    load(path)
        Load a Search instance from a JSON file.

    Examples
    --------
    Create a search with specific parameters:

    >>> search = Search(
    ...     question="What is Python?",
    ...     n_results=5,
    ...     include_languages=["en"],
    ...     publish_start="2023-01-01",
    ...     publish_end="2023-12-31",
    ...     certain=True,
    ... )
    >>> print(search.question)
    What is Python?
    """

    FIELDS = [
        "question",
        "expansions",
        "sql_filter",
        "n_results",
        "n_probes",
        "n_contextify",
        "algorithm",
        "output_type",
        "publish_start",
        "publish_end",
        "include_netlocs",
        "exclude_netlocs",
        "visited_start",
        "visited_end",
        "certain",
        "include_languages",
        "exclude_languages",
        "include_companies",
        "exclude_companies",
        "include_docs",
        "exclude_docs",
    ]

    def __init__(
        self,
        question: str = None,
        expansions: list[str] = None,
        sql_filter: str = None,
        n_results: int = None,
        n_probes: int = None,
        n_contextify: int = None,
        algorithm: str = None,
        output_type: str = None,
        publish_start: str = None,
        publish_end: str = None,
        include_netlocs: list[str] = None,
        exclude_netlocs: list[str] = None,
        visited_start: str = None,
        visited_end: str = None,
        certain: bool = None,
        include_languages: list[str] = None,
        exclude_languages: list[str] = None,
        include_companies: list[str] = None,
        exclude_companies: list[str] = None,
        include_docs: list[str] = None,
        exclude_docs: list[str] = None,
    ) -> None:
        """
        Parameters
        ----------
        question : str, optional
            The main search question or query.
        expansions : list of str, optional
            List of query expansions or related terms.
        sql_filter : str, optional
            Additional SQL filter to apply to the search.
        n_results : int, optional
            Number of results to return.
        n_probes : int, optional
            Number of probe queries to use.
        n_contextify : int, optional
            Number of context documents to retrieve.
        algorithm : str, optional
            Search algorithm to use.
        output_type : str, optional
            Type of output to produce.
        publish_start : str, optional
            Start date for published documents (ISO format).
        publish_end : str, optional
            End date for published documents (ISO format).
        include_netlocs : list of str, optional
            List of netlocs (domains) to include in the search.
        exclude_netlocs : list of str, optional
            List of netlocs (domains) to exclude from the search.
        visited_start : str, optional
            Start date for visited documents (ISO format).
        visited_end : str, optional
            End date for visited documents (ISO format).
        certain : bool, optional
            Whether to only include certain results.
        include_languages : list of str, optional
            Languages to include in the search.
        exclude_languages : list of str, optional
            Languages to exclude from the search.
        include_companies : list of str, optional
            Companies to include in the search.
        exclude_companies : list of str, optional
            Companies to exclude from the search.
        include_docs : list of str, optional
            Document IDs to include in the search.
        exclude_docs : list of str, optional
            Document IDs to exclude from the search.

        Returns
        -------
        None
        """
        self.question = question
        self.expansions = expansions
        self.sql_filter = sql_filter
        self.n_results = n_results
        self.n_probes = n_probes
        self.n_contextify = n_contextify
        self.algorithm = algorithm
        self.output_type = output_type
        self.publish_start = publish_start
        self.publish_end = publish_end
        self.include_netlocs = include_netlocs
        self.exclude_netlocs = exclude_netlocs
        self.visited_start = visited_start
        self.visited_end = visited_end
        self.certain = certain
        self.include_languages = include_languages
        self.exclude_languages = exclude_languages
        self.include_companies = include_companies
        self.exclude_companies = exclude_companies
        self.include_docs = include_docs
        self.exclude_docs = exclude_docs

    def __str__(self) -> str:
        """
        Return a readable string representation of the search parameters.
        Only non-None fields are shown, each on its own line for clarity.
        """
        attrs = []
        for attr in self.FIELDS:
            value = getattr(self, attr)
            if value is not None:
                attrs.append(f"    {attr} = {value!r}")
        if not attrs:
            return "Search()"
        return "Search(\n" + ",\n".join(attrs) + "\n)"

    def __add__(self, other: Search) -> SearchSet:
        """
        Combine two Search instances into a SearchSet.

        This method allows for easy aggregation of multiple search configurations
        into a single collection, which can then be iterated over or processed as a
        group.

        Parameters
        ----------
        other : Search
            Another Search instance to combine with the current one.

        Returns
        -------
        SearchSet
            A new SearchSet containing both the current and the other Search instance.

        Examples
        --------
        >>> search1 = Search(question="What is Python?")
        >>> search2 = Search(question="What is AI?")
        >>> combined = search1 + search2
        >>> print(len(combined.searches))
        2
        """
        from nosible.classes.search_set import SearchSet

        return SearchSet([self, other])

    def to_dict(self) -> dict:
        """
        Convert the Search instance into a dictionary.

        Iterates over all fields defined in the `FIELDS` class attribute and
        constructs a dictionary mapping each field name to its value in the
        current instance. This is useful for serialization, storage, or
        interoperability with APIs expecting dictionary input.

        Returns
        -------
        dict
            A dictionary representation of the search parameters, where keys
            are field names and values are the corresponding attribute values.

        Examples
        --------
        >>> search = Search(
        ...     question="What is Python?", n_results=5, include_languages=["en"], publish_start="2023-01-01"
        ... )
        >>> search.to_dict()["question"]
        'What is Python?'
        """
        return {field: getattr(self, field) for field in self.FIELDS}

    @classmethod
    def from_dict(cls, data: dict) -> Search:
        """
        Construct a Search instance from a dictionary.

        This class method creates a new Search object by mapping the keys in the
        provided dictionary to the corresponding fields of the Search class. Any
        missing fields will be set to None by default.

        Parameters
        ----------
        data : dict
            Dictionary containing search parameters as keys and their values.

        Returns
        -------
        Search
            A Search instance initialized with the values from the dictionary.

        Examples
        --------
        >>> params = {"question": "What is Python?", "n_results": 10, "publish_start": "2023-01-01", "certain": True}
        >>> search = Search.from_dict(params)
        >>> print(search.question)
        What is Python?
        """
        return cls(**{field: data.get(field) for field in cls.FIELDS})

    def save(self, path: str) -> None:
        """
        Save the current Search instance to a JSON file.

        Saves the search parameters to a file in JSON format using the
        `json_dumps` utility. This allows for easy persistence and later
        retrieval of search configurations.

        Parameters
        ----------
        path : str
            The file path where the JSON data will be written.

        Raises
        ------
        IOError
            If the file cannot be written.
        TypeError
            If serialization of the search parameters fails.

        Examples
        --------
        >>> search = Search(
        ...     question="What is Python?", n_results=5, include_languages=["en"], publish_start="2023-01-01"
        ... )
        >>> search.save("search.json")
        """
        data = json_dumps(self.to_dict())
        with open(path, "w") as f:
            f.write(data)

    @classmethod
    def load(cls, path: str) -> Search:
        """
        Load a Search instance from a JSON file.

        Reads the specified file, parses its JSON content, and constructs a
        Search object using the loaded parameters. This method is useful for
        restoring search configurations that were previously saved to disk.

        Parameters
        ----------
        path : str
            The file path from which to load the Search parameters.

        Returns
        -------
        Search
            An instance of the Search class initialized with the loaded parameters.

        Raises
        ------
        IOError
            If the file cannot be read.
        json.JSONDecodeError
            If the file content is not valid JSON.

        Examples
        --------
        Save and load a Search instance:

        >>> search = Search(
        ...     question="What is Python?", n_results=3, include_languages=["en"], publish_start="2023-01-01"
        ... )
        >>> search.save("search.json")
        >>> loaded_search = Search.load("search.json")
        >>> print(loaded_search.question)
        What is Python?
        """
        with open(path) as f:
            data = json_loads(f.read())
        return cls(**data)
