from collections.abc import Iterator
from dataclasses import dataclass, field

from nosible.classes.search import Search
from nosible.utils.json_tools import json_dumps, json_loads


@dataclass()
class SearchSet(Iterator[Search]):
    """
    Manages an iterable collection of Search objects.

    This class provides methods for managing a collection of Search instances,
    including adding, removing, serializing, saving, loading, and clearing the collection.
    It supports iteration, indexing, and conversion to and from JSON-compatible formats.

    Parameters
    ----------
    searches : list of Search
        The list of Search objects in the collection.

    Examples
    --------
    >>> s1 = Search(question="What is Python?", n_results=3)
    >>> s2 = Search(question="What is PEP8?", n_results=2)
    >>> searches = SearchSet([s1, s2])
    >>> print(searches)
    0: What is Python?
    1: What is PEP8?
    >>> searches.add(Search(question="What is AI?", n_results=1))
    >>> searches.to_json("searches.json")
    >>> loaded = SearchSet.from_json("searches.json")
    >>> print(loaded[2].question)
    What is AI?
    """

    searches: list[Search] = field(default_factory=list)
    """ A list of Search objects in the collection."""
    _index: int = field(default=0, init=False, repr=False, compare=False)
    """ Internal index for iteration over searches."""

    def __iter__(self) -> "SearchSet":
        """
        Reset iteration and return self.
        This method is called when the iterator is initialized, allowing iteration over the SearchSet.

        Returns
        -------
        SearchSet
        """
        self._index = 0
        return self

    def __next__(self) -> Search:
        """
        Return the next Search in the collection or stop iteration.

        Raises
        ------
        StopIteration
            If there are no more searches to return.

        Returns
        -------
        Search
            The next Search instance in the collection.
        """
        if self._index < len(self.searches):
            search = self.searches[self._index]
            self._index += 1
            return search
        raise StopIteration

    def __str__(self) -> str:
        """
        List all questions in the collection, one per line with index.

        Returns
        -------
        str
            A string representation of the SearchSet, showing each search's question with its index.
        """
        return "\n".join(f"{i}: {s.question}" for i, s in enumerate(self.searches))

    def __getitem__(self, index: int) -> Search:
        """
        Get a Search by its index.

        Parameters
        ----------
        index : int
            Index of the search to retrieve.

        Returns
        -------
        Search
            The search at the specified index.

        Raises
        ------
        IndexError
            If index is out of range.
        """
        if 0 <= index < len(self.searches):
            return self.searches[index]
        raise IndexError(f"Index {index} out of range for searches collection of size {len(self.searches)}")

    def __len__(self) -> int:
        """
        Get the number of searches in the collection.

        Returns:
            int: The number of Search instances in the collection.
        """
        return len(self.searches)

    def __add__(self, other: "SearchSet") -> "SearchSet":
        """
        Combine two SearchSet instances into a new SearchSet.

        Parameters
        ----------
        other : SearchSet
            Another SearchSet instance to combine with.

        Returns
        -------
        SearchSet
            A new SearchSet containing searches from both instances.

        Raises
        ------
        TypeError
            If 'other' is not a SearchSet instance.
        """
        if not isinstance(other, SearchSet):
            raise TypeError("Can only add another SearchSet instance")
        return SearchSet(self.searches + other.searches)

    def __setitem__(self, index: int, value: Search) -> None:
        """
        Set a Search at a specific index.

        Parameters
        ----------
        index : int
            Index to set the search at.
        value : Search
            The Search instance to set.

        Raises
        ------
        IndexError
            If index is out of range.
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

    def to_dicts(self) -> list[dict]:
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
        >>> searches.to_dicts()[1]["question"]
        'What is PEP8?'
        """
        return [s.to_dict() for s in self.searches]

    def to_json(self, path: str = None) -> str:
        """
        Convert the entire SearchSet collection to a JSON string or save to a file.

        If a file path is provided, the JSON string is saved to that file.
        Otherwise, the JSON string is returned.

        Parameters
        ----------
        path : str, optional
            The file path where the JSON data will be written. If not provided,
            the JSON string is returned.

        Returns
        -------
        str
            A JSON string representation of the SearchSet collection if no path is provided.

        Raises
        -------
        RuntimeError
            If there is an error during serialization or file writing.

        Examples
        --------
        >>> s1 = Search(question="What is Python?", n_results=3)
        >>> s2 = Search(question="What is PEP8?", n_results=2)
        >>> searches = SearchSet([s1, s2])
        >>> json_str = searches.to_json()
        >>> isinstance(json_str, str)
        True
        >>> searches.to_json(
        ...     "searches.json"
        ... )  # The file 'searches.json' will contain both search queries in JSON format.
        """
        try:
            json_bytes = json_dumps(self.to_dicts())
            if path:
                try:
                    with open(path, "w") as f:
                        f.write(json_bytes)
                    return None
                except Exception as e:
                    raise RuntimeError(f"Failed to write JSON to '{path}': {e}") from e
            return json_bytes
        except Exception as e:
            raise RuntimeError(f"Failed to serialize results to JSON: {e}") from e

    @classmethod
    def from_json(cls, path: str) -> "SearchSet":
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

        Examples
        --------
        Save and load a SearchSet collection:

        >>> s1 = Search(question="Python basics", n_results=2)
        >>> s2 = Search(question="PEP8 guidelines", n_results=1)
        >>> searches = SearchSet([s1, s2])
        >>> searches.to_json("searches.json")
        >>> loaded_searches = SearchSet.from_json("searches.json")
        >>> print([s.question for s in loaded_searches])
        ['Python basics', 'PEP8 guidelines']
        """
        with open(path) as f:
            raw = f.read()
            data_list = json_loads(raw)
        searches = [Search(**item) for item in data_list]
        return cls(searches)
