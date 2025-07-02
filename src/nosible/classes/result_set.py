from __future__ import annotations

from collections.abc import Iterator

import duckdb
import pandas as pd
import polars as pl
from tantivy import Document, Index, SchemaBuilder

from nosible.classes.result import Result
from nosible.utils.json_tools import json_dumps, json_loads


class ResultSet(Iterator[Result]):
    """
    Container class for managing and processing a sequence of Result objects.

    This class provides methods for iterating, accessing, and converting collections of
    Result instances. It supports context management, sequence operations, and
    conversion to and from various data formats (CSV, JSON, DataFrames, etc.).

    Attributes
    ----------
    results : list of Result
        The list of Result objects contained in the ResultSet.

    Methods
    -------
    analyze(by="published")
        Analyze the ResultSet by grouping on a specified field.
    find_in_search_results(query, top_k=10)
        Perform an in-memory search over the ResultSet using Tantivy.
    to_csv(file_path=None, delimiter=",", encoding="utf-8")
        Serialize the search results to a CSV file.
    to_polars()
        Convert the search results to a Polars DataFrame.
    to_pandas()
        Convert the search results to a pandas DataFrame.
    to_json(file_path=None, indent=2)
        Serialize the search results to a JSON string or file.
    to_dicts()
        Return the search results as a list of dictionaries.
    to_dict()
        Return the search results as a dictionary keyed by url_hash.
    to_ndjson(file_path=None)
        Serialize search results to newline-delimited JSON (NDJSON).
    to_parquet(file_path=None)
        Serialize the search results to Apache Parquet format.
    to_arrow(file_path=None)
        Serialize the search results to Apache Arrow IPC (Feather) format.
    to_duckdb(file_path=None, table_name="results")
        Serialize the search results to a DuckDB database file and table.
    from_csv(file_path)
        Load search results from a CSV file.
    from_json(file_path)
        Load search results from a JSON file.
    from_polars(df)
        Create a ResultSet from a Polars DataFrame.
    from_pandas(df)
        Create a ResultSet from a pandas DataFrame.
    from_ndjson(file_path)
        Load search results from a NDJSON file.
    from_parquet(file_path)
        Load search results from a Parquet file.
    from_arrow(file_path)
        Load search results from an Arrow IPC file.
    from_duckdb(file_path)
        Load search results from a DuckDB database file.
    from_dicts(dicts)
        Create a ResultSet from a list of dictionaries.
    from_dict(data)
        Create a ResultSet from a dictionary or list of dictionaries.

    Examples
    --------
    >>> from nosible import Result, ResultSet
    >>> results = [
    ...     Result(url="https://example.com", title="Example Domain"),
    ...     Result(url="https://openai.com", title="OpenAI"),
    ... ]
    >>> search_results = ResultSet(results)
    >>> len(search_results)
    2
    >>> for result in search_results:
    ...     print(result.title)
    Example Domain
    OpenAI
    >>> df = search_results.to_pandas()
    >>> list(df.columns)  # doctest: +ELLIPSIS
    ['url', 'title', 'description', 'netloc', 'published', 'visited', 'author', 'content', ... 'url_hash']
    """

    FIELDS = [
        "url",
        "title",
        "description",
        "netloc",
        "published",
        "visited",
        "author",
        "content",
        "language",
        "similarity",
        "url_hash",
    ]

    def __init__(self, results: list[Result] | None = None) -> None:
        self.results: list[Result] = results or []
        self._index: int = 0

    def _as_dicts(self):
        """
        Convert the ResultSet to a list of dictionaries.

        Returns
        -------
        list of dict
            List of dictionaries representing each Result.
        """

        # dataclass.asdict handles nested structures too
        return [r.to_dict() for r in self.results]

    def _as_columns(self):
        """
        Convert the ResultSet to a dictionary of lists, suitable for DataFrame creation.

        Returns
        -------
        dict
            Dictionary where keys are field names and values are lists of field values.
        """

        return {f: [getattr(r, f) for r in self.results] for f in self.FIELDS}

    def __len__(self) -> int:
        """
        Return the number of search results.

        Returns
        -------
        int
            The number of Result objects in the results list.
        """
        return len(self.results)

    def __str__(self) -> str:
        """
        Return a string representation of the ResultSet.

        Returns
        -------
        str
            A formatted table showing the index, similarity, and title of each Result.

        Examples
        --------
        >>> from nosible import Result, ResultSet
        >>> results = [
        ...     Result(url="https://example.com", title="Example Domain", similarity=0.95),
        ...     Result(url="https://openai.com", title="OpenAI", similarity=0.99),
        ... ]
        >>> search_results = ResultSet(results)
        >>> print(search_results)  # doctest: +NORMALIZE_WHITESPACE
        Idx | Similarity | Title
        ------------------------
          0 |   0.95 | Example Domain
          1 |   0.99 | OpenAI

        >>> empty = ResultSet([])
        >>> print(empty)
        ResultSet: No results found.
        """
        if not self.results:
            return "ResultSet: No results found."

        # Create a formatted string for each result
        lines = []
        for idx, result in enumerate(self.results):
            similarity = f"{result.similarity:.2f}" if result.similarity is not None else "N/A"
            title = result.title or "No Title"
            lines.append(f"{idx:>3} | {similarity:>6} | {title}")

        # Add a header
        header = "Idx | Similarity | Title"
        separator = "-" * len(header)
        lines.insert(0, header)
        lines.insert(1, separator)
        # Join all lines into a single string
        return "\n".join(lines)

    def __repr__(self) -> str:
        """
        Returns a string representation of the object for interactive sessions.

        Returns
        -------
        str
            The string representation of the object, as returned by `__str__()`.
        """
        return self.__str__()

    def __iter__(self) -> ResultSet:
        """
        Reset iteration and return self.

        Returns
        -------
        ResultSet
            Iterator over the ResultSet instance.
        """
        self._index = 0
        return self

    def __next__(self) -> Result:
        """
        Returns the next Result in the sequence.

        Returns
        -------
        Result
            The next Result object in the sequence.
        Raises
        ------
        StopIteration
            If the end of the sequence is reached.
        """
        if self._index < len(self.results):
            item = self.results[self._index]
            self._index += 1
            return item
        raise StopIteration

    def __enter__(self) -> ResultSet:
        """
        Enters the runtime context related to this object.

        Returns
        -------
        ResultSet
            The context manager instance itself.
        """
        # Setup if required
        return self

    def __getitem__(self, key: int) -> Result:
        """
        Get a Result by index.

        Parameters
        ----------
        key : int
            Index of the result to retrieve.

        Returns
        -------
        Result
            The Result at the specified index.

        Raises
        ------
        IndexError
            If index is out of range.
        """
        if 0 <= key < len(self.results):
            return self.results[key]
        raise IndexError(f"Index {key} out of range for ResultSet with length {len(self.results)}.")

    def __setitem__(self, key: int, value: Result) -> None:
        """
        Set a Result at a specific index.

        Parameters
        ----------
        key : int
            Index to set the result at.
        value : Result
            Result to set at the specified index.

        Raises
        ------
        IndexError
            If index is out of range.
        """
        if 0 <= key < len(self.results):
            self.results[key] = value
        else:
            raise IndexError(f"Index {key} out of range for ResultSet with length {len(self.results)}.")

    def __add__(self, other: ResultSet) -> ResultSet:
        """
        Concatenate two ResultSet instances.

        Parameters
        ----------
        other : ResultSet
            Another ResultSet instance to concatenate with.

        Returns
        -------
        ResultSet
            A new ResultSet instance containing results from both instances.

        Examples
        --------
        >>> results1 = ResultSet([Result(url="https://example.com")])
        >>> results2 = ResultSet([Result(url="https://openai.com")])
        >>> combined = results1 + results2
        >>> len(combined)
        2
        """
        if not isinstance(other, ResultSet):
            raise TypeError("Can only concatenate ResultSet with another ResultSet.")
        return ResultSet(self.results + other.results)

    def __sub__(self, other: ResultSet) -> ResultSet:
        """
        Subtract another ResultSet from this one, returning a new ResultSet with results not in the other.

        Parameters
        ----------
        other : ResultSet
            Another ResultSet instance to subtract from this one.

        Returns
        -------
        ResultSet
            A new ResultSet instance containing results from this instance that are not in the other.

        Examples
        --------
        >>> results1 = ResultSet([Result(url="https://example.com")])
        >>> results2 = ResultSet([Result(url="https://openai.com")])
        >>> difference = results1 - results2
        >>> len(difference)
        1
        """
        if not isinstance(other, ResultSet):
            raise TypeError("Can only subtract ResultSet with another ResultSet.")
        # Use url_hash for set-based difference if available, else fallback to object identity
        other_hashes = {r.url_hash for r in other.results if r.url_hash}
        if other_hashes:
            filtered = [r for r in self.results if r.url_hash not in other_hashes]
        else:
            # Fallback: use object identity (slower)
            filtered = [r for r in self.results if r not in other.results]
        return ResultSet(filtered)

    def __del__(self) -> None:
        """
        Cleanup resources when the ResultSet instance is deleted. TODO
        """
        self.close()

    def close(self) -> None:
        """
        Explicitly release any held resources.
        """
        # TODO: cleanup handles, sessions, etc.
        pass

    def analyze(self, by: str = "published") -> dict:
        """
        Analyze ResultSet by grouping on a specified field.

        This method uses Polars to compute different metrics based on the `by` parameter:

        - **Date fields** (`"published"` or `"visited"`): Counts per month.
        - **Similarity**: Descriptive statistics.
        - **Categorical fields**: value counts sorted descending, mapping each value to its frequency.

        Parameters
        ----------
        by : str
            The Result attribute to analyze. Must be one of:
            'netloc', 'published', 'visited', 'author', 'language',
             or 'similarity'

        Returns
        -------
        dict
            A dictionary of analysis results. The structure depends on `by`:

            - Date-based fields: { 'YYYY-MM': int(count), ... }
            - Numeric fields: { 'count': float, 'mean': float, 'std': float,
                                'min': float, '25%': float, '50%': float,
                                '75%': float, 'max': float }
            - Categorical fields: { value: int(count), ... } sorted by count descending.

        Examples
        --------
        >>> from nosible import Nosible
        >>> from nosible import Result, ResultSet
        >>> with Nosible() as nos:
        ...     results: ResultSet = nos.search(question="Aircraft Manufacturing", n_results=100)
        ...     summary = results.analyze(by="language")
        ...     print(summary)
        {'en': 100}
        """
        # Convert to Polars DataFrame
        df: pl.DataFrame = self.to_polars()

        # Validate column
        if by not in ["netloc", "published", "visited", "author", "language", "similarity"]:
            raise ValueError(f"Cannot analyze by '{by}' - not a valid field.")

        # Drop nulls for the analysis column
        df = df.drop_nulls(by)
        if df.is_empty():
            return {}

        # Handle author unknown
        if by == "author":
            df = df.with_columns(
                pl.when(pl.col("author").str.strip() == "")
                .then(pl.lit("Author Unknown"))
                .otherwise(pl.col("author"))
                .alias("author")
            )

        # Handle date fields: 'published' or 'visited'
        if by in ("published", "visited"):
            # parse ISO date strings to Date
            df = df.with_columns(pl.col(by).str.strptime(pl.Date, "%Y-%m-%d", strict=False).alias(by))
            # Extract year-month
            df = df.with_columns(pl.col(by).dt.strftime("%Y-%m").alias("year_month"))
            # Count per month
            vc = df.groupby("year_month").agg(pl.count().alias("count")).sort("year_month")
            rows = vc.rows()
            if not rows:
                return {}
            # Generate full month range
            first_month, last_month = rows[0][0], rows[-1][0]
            all_months = pd.date_range(start=f"{first_month}-01", end=f"{last_month}-01", freq="MS").strftime("%Y-%m")
            result = dict.fromkeys(all_months, 0)
            # Fill actual counts
            for month, cnt in rows:
                result[month] = cnt
            return result

        # Non-date: analyze numeric vs. categorical Non-date: analyze numeric vs. categorical
        series = df[by]
        dtype = series.dtype
        # Numeric analysis: descriptive stats
        if dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32):
            desc_df = series.describe()
            return {row[0]: float(row[1]) for row in desc_df.rows()}
        # Categorical/value counts
        vc = series.value_counts()
        _, count_col = vc.columns
        sorted_vc = vc.sort(count_col, descending=True)
        return {str(row[0]): int(row[1]) for row in sorted_vc.rows()}

    def find_in_search_results(self, query: str, top_k: int = 10) -> ResultSet:
        """
        Perform an in-memory search over a ResultSet collection using Tantivy.

        Parameters
        ----------
        query : str
            The search string to rank within these results.
        top_k : int, default=10
            Number of top results to return.

        Returns
        -------
        ResultSet
            A new ResultSet instance containing the top_k results ranked by relevance to `query`.

        Examples
        --------
        >>> from nosible import Nosible
        >>> from nosible import ResultSet
        >>> with Nosible() as nos:
        ...     results: ResultSet = nos.search(question="Aircraft Manufacturing", n_results=10)
        ...     inner = results.find_in_search_results("embraer", top_k=5)
        >>> print(f"Top {len(inner)} hits for “embraer” within the initial results:")
        Top 5 hits for “embraer” within the initial results:
        >>> for idx, hit in enumerate(inner, start=1):
        ...     print("Document returned")
        Document returned
        Document returned
        Document returned
        Document returned
        Document returned
        """
        # Build the Tantivy schema
        schema_builder = SchemaBuilder()
        # Int for doc retrieval.
        schema_builder.add_integer_field("doc_id", stored=True)
        # Content will hold the concatenated text you want to search.
        schema_builder.add_text_field("content", stored=True)
        schema = schema_builder.build()

        # Create in-memory index and writer.
        index = Index(schema)

        # 15MB of RAM reserved (minimum you can).
        writer = index.writer(heap_size=15_000_000, num_threads=1)

        # Index each Result
        for idx, result in enumerate(self.results):
            parts = [result.title or "", result.description or "", result.content or ""]
            full_text = " ".join(p for p in parts if p)

            doc = Document()
            # Pass field names as strings.
            doc.add_integer("doc_id", idx)
            doc.add_text("content", full_text)
            writer.add_document(doc)
        # Flushes and writes the inverted index.
        writer.commit()
        # Makes that new data visible to searchers.
        index.reload()

        # Search the in-memory index
        searcher = index.searcher()
        tantivy_query = index.parse_query(query, ["content"])

        # Map Tantivy hits back to original indices
        hits = searcher.search(tantivy_query, top_k).hits
        matched_idxs = [searcher.doc(addr).get_first("doc_id") for (_score, addr) in hits]
        top_results = [self.results[i] for i in matched_idxs]

        # Pad out to top_k with the remaining docs, in original order.
        if len(top_results) < top_k:
            for i, doc in enumerate(self.results):
                if i not in matched_idxs:
                    top_results.append(doc)
                    if len(top_results) == top_k:
                        break

        return ResultSet(top_results)

    # Conversion methods
    def to_csv(self, file_path: str | None = None, delimiter: str = ",", encoding: str = "utf-8") -> str:
        """
        Serialize the search results to a CSV file.

        This method writes the current ResultSet to a CSV file using Python's built-in
        csv module. Each Result is converted to a dictionary and written as a row.
        The CSV will contain all fields defined in the FIELDS class attribute.

        Parameters
        ----------
        file_path : str or None, optional
            Path to save the CSV file. If None, defaults to "search_results.csv".
        delimiter : str, optional
            Delimiter to use in the CSV file. Default is ','.
        encoding : str, optional
            Encoding for the CSV file. Default is "utf-8".

        Returns
        -------
        str
            The path to the written CSV file.

        Raises
        ------
        RuntimeError
            If writing to the CSV file fails.

        Examples
        --------
        >>> from nosible import Result, ResultSet
        >>> results = [
        ...     Result(url="https://example.com", title="Example Domain"),
        ...     Result(url="https://openai.com", title="OpenAI"),
        ... ]
        >>> search_results = ResultSet(results)
        >>> path = search_results.to_csv("out.csv")
        >>> path.endswith(".csv")
        True
        """
        import csv

        out = file_path or "search_results.csv"
        try:
            with open(out, "w", newline="", encoding=encoding) as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDS, delimiter=delimiter)
                writer.writeheader()
                for result in self.results:
                    writer.writerow(result.to_dict())
        except Exception as e:
            raise RuntimeError(f"Failed to write CSV to '{out}': {e}") from e
        return out

    def to_polars(self) -> pl.DataFrame:
        """
        Convert the search results to a Polars DataFrame.

        Returns
        -------
        pl.DataFrame
            A Polars DataFrame containing all search results, with columns for each field.

        Examples
        --------
        >>> from nosible import Result, ResultSet
        >>> results = [
        ...     Result(url="https://example.com", title="Example Domain"),
        ...     Result(url="https://openai.com", title="OpenAI"),
        ... ]
        >>> search_results = ResultSet(results)
        >>> df = search_results.to_polars()
        >>> isinstance(df, pl.DataFrame)
        True
        >>> "url" in df.columns
        True
        """
        return pl.DataFrame(self._as_columns())

    def to_pandas(self) -> pd.DataFrame:
        """
        Convert the search results to a pandas DataFrame.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing all search results, with columns for each field.

        Examples
        --------
        >>> from nosible import Result, ResultSet
        >>> results = [
        ...     Result(url="https://example.com", title="Example Domain"),
        ...     Result(url="https://openai.com", title="OpenAI"),
        ... ]
        >>> search_results = ResultSet(results)
        >>> df = search_results.to_pandas()
        >>> import pandas as pd
        >>> isinstance(df, pd.DataFrame)
        True
        >>> {"url", "title"}.issubset(df.columns)
        True
        """
        try:
            return self.to_polars().to_pandas()
        except Exception as e:
            raise RuntimeError(f"Failed to convert search results to Pandas DataFrame: {e}") from e

    def to_json(self, file_path: str | None = None) -> str:
        """
        Serialize the search results to a JSON string and optionally write to disk.

        Parameters
        ----------
        file_path : str or None, optional
            Path to save the JSON file. If None, the JSON string is returned.

        Returns
        -------
        str
            The JSON string if `file_path` is None, otherwise the JSON string that was written to file.

        Examples
        --------
        >>> from nosible import Result, ResultSet
        >>> results = [
        ...     Result(url="https://example.com", title="Example Domain"),
        ...     Result(url="https://openai.com", title="OpenAI"),
        ... ]
        >>> search_results = ResultSet(results)
        >>> json_str = search_results.to_json()
        >>> isinstance(json_str, str)
        True
        >>> # Optionally write to file
        >>> path = search_results.to_json(file_path="results.json")
        >>> path.endswith(".json")
        True
        """
        try:
            json_bytes = json_dumps(self._as_dicts())
            if file_path:
                try:
                    with open(file_path, "w") as f:
                        f.write(json_bytes)
                    return file_path
                except Exception as e:
                    raise RuntimeError(f"Failed to write JSON to '{file_path}': {e}") from e
            return json_bytes
        except Exception as e:
            raise RuntimeError(f"Failed to serialize results to JSON: {e}") from e

    def to_dicts(self) -> list[dict]:
        """
        Return the search results as a list of dictionaries.

        Each Result in the collection is converted to a dictionary
        containing all its fields. This is useful for serialization,
        inspection, or further processing.

        Returns
        -------
        list of dict
            List where each element is a dictionary representation of a Result.

        Examples
        --------
        >>> from nosible import Result, ResultSet
        >>> results = [
        ...     Result(url="https://example.com", title="Example Domain"),
        ...     Result(url="https://openai.com", title="OpenAI"),
        ... ]
        >>> search_results = ResultSet(results)
        >>> dict_list = search_results.to_dicts()
        >>> isinstance(dict_list, list)
        True
        >>> isinstance(dict_list[0], dict)
        True
        >>> "url" in dict_list[0]
        True
        """
        try:
            return self._as_dicts()
        except Exception as e:
            raise RuntimeError(f"Failed to convert results to list of dicts: {e}") from e

    def to_dict(self) -> dict:
        """
        Return the search results as a dictionary keyed by `url_hash`.

        Each entry in the returned dictionary maps a unique `url_hash` to the
        corresponding search result's dictionary representation. Only results
        with a non-empty `url_hash` are included.

        Returns
        -------
        dict
            Dictionary mapping `url_hash` (str) to the result dictionary.

        Examples
        --------
        >>> from nosible import Result, ResultSet
        >>> results = [
        ...     Result(url="https://example.com", url_hash="abc123", title="Example Domain"),
        ...     Result(url="https://openai.com", url_hash="def456", title="OpenAI"),
        ... ]
        >>> search_results = ResultSet(results)
        >>> result_dict = search_results.to_dict()
        >>> isinstance(result_dict, dict)
        True
        >>> list(result_dict.keys())
        ['abc123', 'def456']
        >>> result_dict["abc123"]["title"]
        'Example Domain'
        """
        try:
            return {r.url_hash: r.to_dict() for r in self.results if r.url_hash}
        except Exception as e:
            raise RuntimeError(f"Failed to convert results to dict: {e}") from e

    def to_ndjson(self, file_path: str | None = None) -> str:
        """
        Serialize search results to newline-delimited JSON (NDJSON) format.

        Each search result is serialized as a single JSON object per line.
        The resulting NDJSON string can be written to disk or returned as a string.

        Parameters
        ----------
        file_path : str or None, optional
            Path to save the NDJSON file. If None, returns the NDJSON string.
            Default is None.

        Returns
        -------
        str
            File path if written to file, otherwise the NDJSON string.

        Examples
        --------
        >>> from nosible import Result, ResultSet
        >>> results = [
        ...     Result(url="https://example.com", title="Example Domain"),
        ...     Result(url="https://openai.com", title="OpenAI"),
        ... ]
        >>> search_results = ResultSet(results)
        >>> ndjson_str = search_results.to_ndjson()
        >>> print(ndjson_str.splitlines()[0][0:30])
        {"url": "https://example.com",
        >>> # Optionally write to file
        >>> path = search_results.to_ndjson(file_path="results.ndjson")
        >>> path.endswith(".ndjson")
        True
        """
        try:
            lines = "\n".join(json_dumps(d) for d in self._as_dicts())
            if file_path:
                try:
                    with open(file_path, "w") as f:
                        f.write(lines)
                    return file_path
                except Exception as e:
                    raise RuntimeError(f"Failed to write NDJSON to '{file_path}': {e}") from e
            return lines
        except Exception as e:
            raise RuntimeError(f"Failed to serialize results to NDJSON: {e}") from e

    def to_parquet(self, file_path: str | None = None) -> str:
        """
        Serialize the search results to Apache Parquet format using Polars.

        This method writes the current ResultSet to a Parquet file, which is an efficient
        columnar storage format suitable for analytics and interoperability with data tools.

        Parameters
        ----------
        file_path : str or None, optional
            Path to save the Parquet file. If None, defaults to "results.parquet".

        Returns
        -------
        str
            The path to the written Parquet file.

        Raises
        ------
        RuntimeError
            If writing to the Parquet file fails.

        Examples
        --------
        >>> from nosible import Result, ResultSet
        >>> results = [
        ...     Result(url="https://example.com", title="Example Domain"),
        ...     Result(url="https://openai.com", title="OpenAI"),
        ... ]
        >>> search_results = ResultSet(results)
        >>> parquet_path = search_results.to_parquet("my_results.parquet")
        >>> parquet_path.endswith(".parquet")
        True
        """
        out = file_path or "results.parquet"
        try:
            self.to_polars().write_parquet(out)
        except Exception as e:
            raise RuntimeError(f"Failed to write Parquet to '{out}': {e}") from e
        return out

    def to_arrow(self, file_path: str | None = None) -> str:
        """
        Serialize the search results to Apache Arrow IPC (Feather) format using Polars.

        This method writes the current ResultSet to an Arrow IPC file, which is an efficient
        columnar storage format for fast data interchange and analytics.

        Parameters
        ----------
        file_path : str or None, optional
            Path to save the Arrow IPC file. If None, defaults to "results.arrow".

        Returns
        -------
        str
            The path to the written Arrow IPC file.

        Raises
        ------
        RuntimeError
            If writing to the Arrow IPC file fails.

        Examples
        --------
        >>> from nosible import Result, ResultSet
        >>> results = [
        ...     Result(url="https://example.com", title="Example Domain"),
        ...     Result(url="https://openai.com", title="OpenAI"),
        ... ]
        >>> search_results = ResultSet(results)
        >>> arrow_path = search_results.to_arrow("my_results.arrow")
        >>> arrow_path.endswith(".arrow")
        True
        """
        out = file_path or "results.arrow"
        try:
            self.to_polars().write_ipc(out)
        except Exception as e:
            raise RuntimeError(f"Failed to write Arrow IPC to '{out}': {e}") from e
        return out

    def to_duckdb(self, file_path: str | None = None, table_name: str = "results") -> str:
        """
        Serialize the search results to a DuckDB database file and table.

        This method writes the current ResultSet to a DuckDB database file,
        creating a new table or replacing an existing one with the specified name.
        The table will contain all fields defined in the FIELDS class attribute.

        Parameters
        ----------
        file_path : str or None, optional
            Path to save the DuckDB file. If None, defaults to "results.duckdb".
        table_name : str, optional
            Name of the table to write the results to. Default is "results".

        Returns
        -------
        str
            The path to the written DuckDB file.

        Raises
        ------
        RuntimeError
            If writing to the DuckDB file fails.

        Examples
        --------
        >>> from nosible import Result, ResultSet
        >>> results = [
        ...     Result(url="https://example.com", title="Example Domain"),
        ...     Result(url="https://openai.com", title="OpenAI"),
        ... ]
        >>> search_results = ResultSet(results)
        >>> db_path = search_results.to_duckdb(file_path="my_results.duckdb", table_name="search_table")
        >>> db_path.endswith(".duckdb")
        True
        """
        out = file_path or "results.duckdb"
        try:
            import duckdb

            # Convert to Polars DataFrame and then to Arrow Table
            df = self.to_polars()
            # Connect to DuckDB and write the Arrow Table to a table
            con = duckdb.connect(out)
            # Write the DataFrame to the specified table name, replacing if exists
            con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df").df()
            con.close()
            return out

        except Exception as e:
            raise RuntimeError(f"Failed to write DuckDB table to '{out}': {e}") from e

    # Loading from disk
    @classmethod
    def from_csv(cls, file_path: str) -> ResultSet:
        """
        Load search results from a CSV file using Polars.

        Parameters
        ----------
        file_path : str
            Path to the CSV file.

        Returns
        -------
        ResultSet
            An instance of ResultSet containing all loaded results.

        Examples
        --------
        >>> import polars as pl
        >>> from nosible import ResultSet, Result
        >>> # Suppose 'data.csv' contains columns: url,title,description
        >>> _ = pl.DataFrame(
        ...     [
        ...         {"url": "https://example.com", "title": "Example Domain", "description": "Example description"},
        ...         {"url": "https://openai.com", "title": "OpenAI", "description": "AI research"},
        ...     ]
        ... ).write_csv("data.csv")
        >>> results = ResultSet.from_csv("data.csv")
        >>> isinstance(results, ResultSet)
        True
        >>> len(results)
        2
        >>> results[0].title
        'Example Domain'
        """
        try:
            df = pl.read_csv(file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to read CSV file '{file_path}': {e}") from e
        results = []
        for row in df.iter_rows(named=True):
            try:
                result = Result(
                    url=row.get("url"),
                    title=row.get("title"),
                    description=row.get("description"),
                    netloc=row.get("netloc"),
                    published=row.get("published"),
                    visited=row.get("visited"),
                    author=row.get("author"),
                    content=row.get("content"),
                    language=row.get("language"),
                    similarity=row.get("similarity"),
                    url_hash=row.get("url_hash"),
                )
                results.append(result)
            except Exception as e:
                raise ValueError(f"Error parsing row in CSV: {row}\n{e}") from e
        return cls(results)

    @classmethod
    def from_json(cls, file_path: str) -> ResultSet:
        """
        Load search results from a JSON file.

        Parameters
        ----------
        file_path : str
            Path to the JSON file containing search results.

        Returns
        -------
        ResultSet
            An instance of ResultSet containing all loaded results.

        Examples
        --------
        >>> import json
        >>> from nosible import ResultSet
        >>> # Suppose 'data.json' contains:
        >>> # [
        >>> #   {"url": "https://example.com", "title": "Example Domain"},
        >>> #   {"url": "https://openai.com", "title": "OpenAI"}
        >>> # ]
        >>> with open("data.json", "w") as f:
        ...     json.dump(
        ...         [
        ...             {"url": "https://example.com", "title": "Example Domain"},
        ...             {"url": "https://openai.com", "title": "OpenAI"},
        ...         ],
        ...         f,
        ...     )
        >>> results = ResultSet.from_json("data.json")
        >>> isinstance(results, ResultSet)
        True
        >>> len(results)
        2
        >>> results[0].title
        'Example Domain'
        """
        try:
            with open(file_path) as f:
                data = json_loads(f.read())
        except Exception as e:
            raise RuntimeError(f"Failed to read or parse JSON file '{file_path}': {e}") from e
        try:
            return cls.from_dict(data)
        except Exception as e:
            raise RuntimeError(f"Failed to create ResultSet from JSON data in '{file_path}': {e}") from e

    @classmethod
    def from_polars(cls, df: pl.DataFrame) -> ResultSet:
        """
        Create a ResultSet instance from a Polars DataFrame.

        Parameters
        ----------
        df : pl.DataFrame
            Polars DataFrame containing columns corresponding to Result fields.

        Returns
        -------
        ResultSet
            An instance of ResultSet containing all loaded results.

        Examples
        --------
        >>> import polars as pl
        >>> from nosible import ResultSet
        >>> data = [
        ...     {"url": "https://example.com", "title": "Example Domain", "similarity": 0.95},
        ...     {"url": "https://openai.com", "title": "OpenAI", "similarity": 0.99},
        ... ]
        >>> df = pl.DataFrame(data)
        >>> results = ResultSet.from_polars(df)
        >>> isinstance(results, ResultSet)
        True
        >>> len(results)
        2
        >>> results[0].title
        'Example Domain'
        """
        results = []
        for row in df.iter_rows(named=True):
            try:
                result = Result(
                    url=row.get("url"),
                    title=row.get("title"),
                    description=row.get("description"),
                    netloc=row.get("netloc"),
                    published=row.get("published"),
                    visited=row.get("visited"),
                    author=row.get("author"),
                    content=row.get("content"),
                    language=row.get("language"),
                    similarity=row.get("semantics", {}).get("similarity", row.get("similarity")),
                    url_hash=row.get("url_hash"),
                )
                results.append(result)
            except Exception as e:
                raise ValueError(f"Error parsing row in DataFrame: {row}\n{e}") from e
        return cls(results)

    @classmethod
    def from_pandas(cls, df: pd.DataFrame) -> ResultSet:
        """Create a ResultSet instance from a pandas DataFrame.
        This class method converts a given pandas DataFrame to a Polars DataFrame
        and then constructs a ResultSet object from it. This is useful for
        integrating with workflows that use pandas for data manipulation.
        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing the search result fields. Each row should represent
            a single search result, with columns corresponding to the expected fields
            of ResultSet.
        Returns
        -------
        ResultSet
            An instance of ResultSet containing the data from the input DataFrame.
        Examples
        --------
        >>> data = [{"url": "https://example.com", "title": "Example"}]
        >>> df = pd.DataFrame(data)
        >>> print(len(df))
        1
        """
        pl_df = pl.from_pandas(df)
        return cls.from_polars(pl_df)

    @classmethod
    def from_ndjson(cls, file_path: str) -> ResultSet:
        """
        Load search results from a newline-delimited JSON (NDJSON) file.

        Parameters
        ----------
        file_path : str
            Path to the NDJSON file containing search results, where each line is a JSON object.

        Returns
        -------
        ResultSet
            An instance of ResultSet containing all loaded results.

        Raises
        ------
        RuntimeError
            If the file cannot be read.
        ValueError
            If no valid search results are found or a line cannot be parsed.

        Examples
        --------
        Suppose 'data.ndjson' contains:
            {"url": "https://example.com", "title": "Example Domain"}
            {"url": "https://openai.com", "title": "OpenAI"}

        >>> from nosible import ResultSet, Result
        >>> # Write example NDJSON file
        >>> with open("data.ndjson", "w") as f:
        ...     f.write('{"url": "https://example.com", "title": "Example Domain"}\\n')
        ...     f.write('{"url": "https://openai.com", "title": "OpenAI"}\\n')
        58
        49
        >>> results = ResultSet.from_ndjson("data.ndjson")
        >>> isinstance(results, ResultSet)
        True
        >>> len(results)
        2
        >>> results[0].title
        'Example Domain'
        """
        results = []
        try:
            with open(file_path) as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json_loads(line)
                            result = Result(
                                url=data.get("url"),
                                title=data.get("title"),
                                description=data.get("description"),
                                netloc=data.get("netloc"),
                                published=data.get("published"),
                                visited=data.get("visited"),
                                author=data.get("author"),
                                content=data.get("content"),
                                language=data.get("language"),
                                similarity=data.get("similarity"),
                                url_hash=data.get("url_hash"),
                            )
                            results.append(result)
                        except Exception as e:
                            raise ValueError(f"Error parsing NDJSON line: {line}\n{e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to read NDJSON file '{file_path}': {e}") from e
        if not results:
            raise ValueError(f"No valid search results found in the NDJSON file '{file_path}'.")
        return cls(results)

    @classmethod
    def from_parquet(cls, file_path: str) -> ResultSet:
        """
        Load search results from a Parquet file using Polars.

        Parameters
        ----------
        file_path : str
            Path to the Parquet file containing search results.

        Returns
        -------
        ResultSet
            An instance of ResultSet containing all loaded results.

        Raises
        ------
        RuntimeError
            If the file cannot be read or parsed.

        Examples
        --------
        >>> import polars as pl
        >>> from nosible import ResultSet
        >>> # Create a sample Parquet file
        >>> df = pl.DataFrame(
        ...     [
        ...         {"url": "https://example.com", "title": "Example Domain", "similarity": 0.95},
        ...         {"url": "https://openai.com", "title": "OpenAI", "similarity": 0.99},
        ...     ]
        ... )
        >>> df.write_parquet("sample.parquet")
        >>> results = ResultSet.from_parquet("sample.parquet")
        >>> isinstance(results, ResultSet)
        True
        >>> len(results)
        2
        >>> results[0].title
        'Example Domain'
        """
        try:
            df = pl.read_parquet(file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to read Parquet file '{file_path}': {e}") from e
        try:
            return cls.from_polars(df)
        except Exception as e:
            raise RuntimeError(f"Failed to create ResultSet from Parquet data in '{file_path}': {e}") from e

    @classmethod
    def from_arrow(cls, file_path: str) -> ResultSet:
        """
        Load search results from an Apache Arrow IPC (Feather) file using Polars.

        Parameters
        ----------
        file_path : str
            Path to the Arrow IPC file containing search results.

        Returns
        -------
        ResultSet
            An instance of ResultSet containing all loaded results.

        Raises
        ------
        RuntimeError
            If the file cannot be read or parsed.

        Examples
        --------
        >>> import polars as pl
        >>> from nosible import ResultSet
        >>> # Create a sample Arrow IPC file
        >>> df = pl.DataFrame(
        ...     [
        ...         {"url": "https://example.com", "title": "Example Domain", "similarity": 0.95},
        ...         {"url": "https://openai.com", "title": "OpenAI", "similarity": 0.99},
        ...     ]
        ... )
        >>> df.write_ipc("sample.arrow")
        >>> results = ResultSet.from_arrow("sample.arrow")
        >>> isinstance(results, ResultSet)
        True
        >>> len(results)
        2
        >>> results[0].title
        'Example Domain'
        """
        try:
            df = pl.read_ipc(file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to read Arrow IPC file '{file_path}': {e}") from e
        try:
            return cls.from_polars(df)
        except Exception as e:
            raise RuntimeError(f"Failed to create ResultSet from Arrow data in '{file_path}': {e}") from e

    @classmethod
    def from_duckdb(cls, file_path: str) -> ResultSet:
        """
        Load search results from a DuckDB database file.

        This class method reads a DuckDB file, retrieves the first available table,
        and loads its contents as Result objects. The table is expected to have
        columns matching the Result fields.

        Parameters
        ----------
        file_path : str
            Path to the DuckDB database file.

        Returns
        -------
        ResultSet
            An instance of ResultSet containing all loaded results.

        Raises
        ------
        RuntimeError
            If the file cannot be read or parsed.
        ValueError
            If no tables are found in the DuckDB file.

        Examples
        --------
        >>> from nosible import ResultSet, Result
        >>> results = [
        ...     Result(url="https://example.com", title="Example Domain", similarity=0.95),
        ...     Result(url="https://openai.com", title="OpenAI", similarity=0.99),
        ... ]
        >>> search_results = ResultSet(results)
        >>> db_path = search_results.to_duckdb(file_path="results.duckdb", table_name="search_results")
        >>> loaded = ResultSet.from_duckdb("results.duckdb")
        >>> isinstance(loaded, ResultSet)
        True
        >>> len(loaded)
        2
        >>> loaded[0].title
        'Example Domain'
        """
        try:
            con = duckdb.connect(file_path, read_only=True)
        except Exception as e:
            raise RuntimeError(f"Failed to connect to DuckDB file '{file_path}': {e}") from e
        try:
            tables = con.execute("SHOW TABLES").fetchall()
            if not tables:
                raise ValueError(f"No tables found in DuckDB file '{file_path}'.")
            table_name = tables[0][0]
            try:
                arrow_table = con.execute(f"SELECT * FROM {table_name}").arrow()
            except Exception as e:
                raise RuntimeError(
                    f"Failed to fetch data from table '{table_name}' in DuckDB file '{file_path}': {e}"
                ) from e
            df = pl.from_arrow(arrow_table)
        except Exception as e:
            raise RuntimeError(f"Failed to read from DuckDB file '{file_path}': {e}") from e
        finally:
            con.close()
        try:
            return cls.from_polars(df)
        except Exception as e:
            raise RuntimeError(f"Failed to create ResultSet from DuckDB data in '{file_path}': {e}") from e

    @classmethod
    def from_dicts(cls, dicts: list[dict]) -> ResultSet:
        """
        Create a ResultSet instance from a list of dictionaries.

        Each dictionary in the input list should contain keys corresponding to the
        fields of a Result. This method will attempt to construct a Result
        object from each dictionary and collect them into a ResultSet container.

        Parameters
        ----------
        dicts : list of dict
            List where each element is a dictionary representing a Result.

        Returns
        -------
        ResultSet
            An instance containing all successfully parsed Result objects.

        Raises
        ------
        ValueError
            If any dictionary cannot be parsed into a Result.

        Examples
        --------
        >>> from nosible import ResultSet
        >>> dicts = [
        ...     {"url": "https://example.com", "title": "Example Domain", "url_hash": "abc123"},
        ...     {"url": "https://openai.com", "title": "OpenAI", "url_hash": "def456"},
        ... ]
        >>> results = ResultSet.from_dicts(dicts)
        >>> len(results)
        2
        >>> results[0].title
        'Example Domain'
        """
        results = []
        for d in dicts:
            try:
                # Try to get similarity first else go into semantics and get similarity
                result = Result(
                    url=d.get("url"),
                    title=d.get("title"),
                    description=d.get("description"),
                    netloc=d.get("netloc"),
                    published=d.get("published"),
                    visited=d.get("visited"),
                    author=d.get("author"),
                    content=d.get("content"),
                    language=d.get("language"),
                    similarity=d.get("similarity", d.get("semantics", {}).get("similarity")),
                    url_hash=d.get("url_hash"),
                )
                results.append(result)
            except Exception as e:
                raise ValueError(f"Error parsing dictionary into Result: {d}\n{e}") from e
        return cls(results)

    @classmethod
    def from_dict(cls, data: dict | list) -> ResultSet:
        """
        Create a ResultSet instance from a dictionary or a list of dictionaries.

        This method allows for flexible construction of ResultSet from either a single
        dictionary representing one search result, or a list of such dictionaries.

        Parameters
        ----------
        data : dict or list of dict
            A single dictionary or a list of dictionaries, where each dictionary contains
            keys corresponding to Result fields.

        Returns
        -------
        ResultSet
            An instance containing one or more Result objects parsed from the input.

        Raises
        ------
        ValueError
            If the input is neither a dictionary nor a list of dictionaries.

        Examples
        --------
        >>> from nosible import ResultSet
        >>> # From a single dictionary
        >>> single = {"url": "https://example.com", "title": "Example", "url_hash": "abc123"}
        >>> results = ResultSet.from_dict(single)
        >>> isinstance(results, ResultSet)
        True
        >>> len(results)
        1
        >>> results[0].title
        'Example'
        >>> # From a list of dictionaries
        >>> data = [
        ...     {"url": "https://a.com", "title": "A", "url_hash": "a1"},
        ...     {"url": "https://b.com", "title": "B", "url_hash": "b2"},
        ... ]
        >>> results = ResultSet.from_dict(data)
        >>> len(results)
        2
        >>> results[1].title
        'B'
        """
        if isinstance(data, list):
            try:
                return cls.from_dicts(data)
            except Exception as e:
                raise RuntimeError(f"Failed to create ResultSet from list of dicts: {e}") from e
        elif isinstance(data, dict):
            try:
                return cls.from_dicts([data])
            except Exception as e:
                raise RuntimeError(f"Failed to create ResultSet from dict: {e}") from e
        else:
            raise ValueError("Input must be a list of dictionaries or a single dictionary.")


if __name__ == "__main__":
    import doctest

    doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    print("All tests passed!")
