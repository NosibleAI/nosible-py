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
