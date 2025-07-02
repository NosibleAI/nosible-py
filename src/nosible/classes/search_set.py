from collections.abc import Iterator

from nosible.classes.search import Search
from nosible.utils.json_tools import json_dumps, json_loads


class SearchSet(Iterator[Search]):
    """
    Manages an iterable collection of Search objects.

    This class provides methods for managing a collection of Search instances,
    including adding, removing, serializing, saving, loading, and clearing the collection.
    It supports iteration, indexing, and conversion to and from JSON-compatible formats.

    Attributes
    ----------
    searches : list of Search
        The list of Search objects in the collection.

    Methods
    -------
    add(search)
        Add a Search instance to the collection.
    remove(index)
        Remove a Search instance from the collection by its index.
    to_list()
        Convert all Search objects in the collection to a list of dictionaries.
    to_json()
        Convert the entire SearchSet collection to a JSON string.
    save(path)
        Save all Search instances in the collection to a JSON file.
    load(path)
        Load a SearchSet collection from a JSON file.

    Examples
    --------
    >>> s1 = Search(question="What is Python?", n_results=3)
    >>> s2 = Search(question="What is PEP8?", n_results=2)
    >>> searches = SearchSet([s1, s2])
    >>> print(searches)
    0: What is Python?
    1: What is PEP8?
    >>> searches.add(Search(question="What is AI?", n_results=1))
    >>> searches.save("searches.json")
    >>> loaded = SearchSet.load("searches.json")
    >>> print(loaded[2].question)
    What is AI?
    """

    def __init__(self, searches: list[Search] = None) -> None:
        """
        Initializes the object with an optional list of Search instances.

        Parameters
        ----------
        searches : list of Search, optional
            A list of Search objects to initialize the instance with. Defaults to an empty list if not provided.

        Returns
        -------
        None
        """
        self.searches = searches or []
        self._index = 0

    def __iter__(self) -> "SearchSet":
        """
        Reset iteration and return self.
        """
        self._index = 0
        return self

    def __next__(self) -> Search:
        """
        Return the next Search in the collection or stop iteration.
        """
        if self._index < len(self.searches):
            search = self.searches[self._index]
            self._index += 1
            return search
        raise StopIteration

    def __str__(self) -> str:
        """
        List all questions in the collection, one per line with index.
        """
        return "\n".join(f"{i}: {s.question}" for i, s in enumerate(self.searches))

    def __getitem__(self, index: int) -> Search:
        """
        Get a Search by its index.

        Args:
            index (int): Index of the search to retrieve.

        Returns:
            Search: The search at the specified index.

        Raises:
            IndexError: If index is out of range.
        """
        if 0 <= index < len(self.searches):
            return self.searches[index]
        raise IndexError(f"Index {index} out of range for searches collection of size {len(self.searches)}")

    def __setitem__(self, index: int, value: Search) -> None:
        """
        Set a Search at a specific index.

        Args:
            index (int): Index to set the search at.
            value (Search): The Search instance to set.

        Raises:
            IndexError: If index is out of range.
        """
        if 0 <= index < len(self.searches):
            self.searches[index] = value
        else:
            raise IndexError(f"Index {index} out of range for searches collection of size {len(self.searches)}")

    def add(self, search: Search) -> None:
        """
        Add a Search instance to the collection.

        Parameters
        ----------
        search : Search
            The Search instance to add to the collection.

        Examples
        --------
        >>> searches = SearchSet()
        >>> search = Search(question="What is Python?", n_results=3)
        >>> searches.add(search)
        >>> print(len(searches.searches))
        1
        >>> print(searches[0].question)
        What is Python?
        """
        self.searches.append(search)

    def remove(self, index: int) -> None:
        """
        Remove a Search instance from the collection by its index.

        Parameters
        ----------
        index : int
            The index of the Search instance to remove from the collection.

        Raises
        ------
        IndexError
            If the index is out of range.

        Examples
        --------
        Remove a search from the collection by its index:

        >>> s1 = Search(question="First")
        >>> s2 = Search(question="Second")
        >>> s3 = Search(question="Third")
        >>> searches = SearchSet([s1, s2, s3])
        >>> searches.remove(1)
        >>> [s.question for s in searches.searches]
        ['First', 'Third']
        """
        del self.searches[index]

    def to_list(self) -> list[dict]:
        """
        Convert all Search objects in the collection to a list of dictionaries.

        This method serializes each Search instance in the collection to its
        dictionary representation, making it suitable for JSON serialization,
        storage, or interoperability with APIs expecting a list of search
        parameter dictionaries.

        Returns
        -------
        list of dict
            A list where each element is a dictionary representation of a Search
            object in the collection.

        Examples
        --------
        >>> s1 = Search(question="What is Python?", n_results=3)
        >>> s2 = Search(question="What is PEP8?", n_results=2)
        >>> searches = SearchSet([s1, s2])
        >>> searches.to_list()[1]["question"]
        'What is PEP8?'
        """
        return [s.to_dict() for s in self.searches]

    def to_json(self) -> str:
        """
        Convert the entire SearchSet collection to a JSON string.

        Serializes the collection of Search objects into a JSON string format.
        This is useful for storing or transmitting the search configurations in a
        standardized format.

        Returns
        -------
        str
            A JSON string representation of the SearchSet collection.

        Examples
        --------
        >>> s1 = Search(question="What is Python?", n_results=3)
        >>> s2 = Search(question="What is PEP8?", n_results=2)
        >>> searches = SearchSet([s1, s2])
        >>> json_str = searches.to_json()
        >>> isinstance(json_str, str)
        True
        """
        return json_dumps(self.to_list())

    def save(self, path: str) -> None:
        """
        Save all Search instances in the collection to a JSON file.

        Serializes the entire collection of Search objects to a JSON file using
        the `json_dumps` utility. This allows for persistent storage and later
        retrieval of multiple search configurations.

        Parameters
        ----------
        path : str
            The file path where the JSON data will be written.

        Raises
        ------
        IOError
            If the file cannot be written.

        Examples
        --------
        Save a collection of searches to a file:

        >>> s1 = Search(question="Python basics", n_results=2)
        >>> s2 = Search(question="PEP8 guidelines", n_results=1)
        >>> searches = SearchSet([s1, s2])
        >>> searches.save("searches.json")

        # The file 'searches.json' will contain both search queries in JSON format.
        """
        data = json_dumps(self.to_list())
        with open(path, "w") as f:
            f.write(data)

    @classmethod
    def load(cls, path: str) -> "SearchSet":
        """
        Load a SearchSet collection from a JSON file.

        Reads the specified file, parses its JSON content, and constructs a
        SearchSet object containing all loaded Search instances. This method is
        useful for restoring collections of search configurations that were
        previously saved to disk.

        Parameters
        ----------
        path : str
            The file path from which to load the SearchSet collection.

        Returns
        -------
        SearchSet
            An instance of the SearchSet class containing all loaded Search objects.

        Raises
        ------
        IOError
            If the file cannot be read.
        json.JSONDecodeError
            If the file content is not valid JSON.

        Examples
        --------
        Save and load a SearchSet collection:

        >>> s1 = Search(question="Python basics", n_results=2)
        >>> s2 = Search(question="PEP8 guidelines", n_results=1)
        >>> searches = SearchSet([s1, s2])
        >>> searches.save("searches.json")
        >>> loaded_searches = SearchSet.load("searches.json")
        >>> print([s.question for s in loaded_searches])
        ['Python basics', 'PEP8 guidelines']
        """
        with open(path) as f:
            raw = f.read()
            data_list = json_loads(raw)
        searches = [Search(**item) for item in data_list]
        return cls(searches)
