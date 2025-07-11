from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from nosible.utils.json_tools import json_dumps, json_loads, print_dict

if TYPE_CHECKING:
    from nosible.classes.search_set import SearchSet


@dataclass(init=True, repr=True, eq=True)
class Search:
    """
    Represents the parameters for a search operation.

    This class encapsulates all configurable options for performing a search,
    such as the query text, filters, result limits, and algorithm selection.

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
    min_similarity : float
        Results must have at least this similarity score.
    must_include: list of str
        Only results mentioning these strings will be included.
    must_exclude : list of str
        Any result mentioning these strings will be excluded.
    autogenerate_expansions : bool, default=False
        Do you want to generate expansions automatically using a LLM?
    publish_start : str, optional
        Start date for when the document was published (ISO format).
    publish_end : str, optional
        End date for when the document was published (ISO format).
    visited_start : str, optional
        Start date for when the document was visited by NOSIBLE (ISO format).
    visited_end : str, optional
        End date for when the document was visited by NOSIBLE (ISO format).
    certain : bool, optional
        Only include documents where we are 100% sure of the date.
    include_netlocs : list of str, optional
        List of netlocs (domains) to include in the search. (Max 50)
    exclude_netlocs : list of str, optional
        List of netlocs (domains) to exclude in the search. (Max 50)
    include_languages : list of str, optional
        Languages to include in the search. (Max 50, ISO 639-1 language codes).
    exclude_languages : list of str, optional
        Language codes to exclude in the search (Max 50, ISO 639-1 language codes).
    include_companies : list of str, optional
        Google KG IDs of public companies to require (Max 50).
    exclude_companies : list of str, optional
        Google KG IDs of public companies to forbid (Max 50).
    include_docs : list of str, optional
        URL hashes of docs to include (Max 50).
    exclude_docs : list of str, optional
        URL hashes of docs to exclude (Max 50).

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

    question: str | None = None
    """The main search question or query."""
    expansions: list[str] | None = None
    """List of query expansions or related terms."""
    sql_filter: str | None = None
    """Additional SQL filter to apply to the search."""
    n_results: int | None = None
    """Number of results to return."""
    n_probes: int | None = None
    """Number of probe queries to use."""
    n_contextify: int | None = None
    """Number of context documents to retrieve."""
    algorithm: str | None = None
    """Search algorithm to use."""
    min_similarity: float | None = None
    """Results must have at least this similarity score."""
    must_include: list[str] | None = None
    """Only results mentioning these strings will be included."""
    must_exclude: list[str] | None = None
    """Any result mentioning these strings will be excluded."""
    autogenerate_expansions: bool = False
    """Do you want to generate expansions automatically using a LLM?"""
    publish_start: str | None = None
    """Start date for when the document was published."""
    publish_end: str | None = None
    """End date for when the document was published."""
    visited_start: str | None = None
    """Start date for when the document was visited by NOSIBLE."""
    visited_end: str | None = None
    """End date for when the document was visited by NOSIBLE."""
    certain: bool | None = None
    """Only include documents where we are 100% sure of the date."""
    include_netlocs: list[str] | None = None
    """List of netlocs (domains) to include in the search (Max 50)."""
    exclude_netlocs: list[str] | None = None
    """List of netlocs (domains) to exclude in the search (Max 50)."""
    include_languages: list[str] | None = None
    """Languages to include in the search. (Max 50)"""
    exclude_languages: list[str] | None = None
    """Language codes to exclude in the search (Max 50)"""
    include_companies: list[str] | None = None
    """Google KG IDs of public companies to require (Max 50)."""
    exclude_companies: list[str] | None = None
    """Google KG IDs of public companies to forbid (Max 50)."""
    include_docs: list[str] | None = None
    """URL hashes of docs to include (Max 50)."""
    exclude_docs: list[str] | None = None
    """URL hashes of docs to exclude (Max 50)."""

    _FIELDS = [
        "question",
        "expansions",
        "sql_filter",
        "n_results",
        "n_probes",
        "n_contextify",
        "algorithm",
        "min_similarity",
        "must_include",
        "must_exclude",
        "autogenerate_expansions",
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

    def __str__(self) -> str:
        """
        Return a readable string representation of the search parameters.
        Only non-None fields are shown, each on its own line for clarity.

        Returns
        -------
        str
            A string representation of the Search instance, showing only the
        """
        return print_dict(self.to_dict())

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
        return asdict(self, dict_factory=dict)

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
        return cls(**{field: data.get(field) for field in cls._FIELDS})

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
