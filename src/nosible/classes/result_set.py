"""Collection model and format adapters for NOSIBLE Search results."""

import os
import csv
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import duckdb
import pandas as pd
import polars as pl
from tantivy import Document, Index, SchemaBuilder

import nosible.classes.result
from nosible.utils.json_tools import json_dumps, json_loads

RESULT_FIELD_ORDER: List[str] = [
    "url",
    "title",
    "description",
    "netloc",
    "published",
    "visited",
    "author",
    "content",
    "best_chunk",
    "language",
    "similarity",
    "url_hash",
    "brand_safety",
    "continent",
    "region",
    "country",
    "sector",
    "industry_group",
    "industry",
    "sub_industry",
    "iab_tier_1",
    "iab_tier_2",
    "iab_tier_3",
    "iab_tier_4",
    "semantics"
]
CSV_PRESENT_FIELDS_COLUMN = "__nosible_present_fields__"
CSV_ENCODED_FIELDS_COLUMN = "__nosible_encoded_fields__"
CSV_ESCAPED_FIELD_PREFIX = "__nosible_escaped_field__"
SAFE_TABLE_NAME = re.compile(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class ResultSet(Iterator[Any]):
    """Ordered, iterable collection of NOSIBLE Search results."""

    results: List[Any] = field(default_factory=list)
    message: Optional[str] = field(
        default=None,
        compare=False
    )
    query: Optional[Dict[str, Any]] = field(
        default=None,
        compare=False
    )
    index: int = field(
        default=0,
        init=False,
        repr=False,
        compare=False
    )

    def __len__(
        self: "ResultSet"
    ) -> int:
        """
        Return the number of results.

        :return: Number of results.
        """
        return len(self.results)

    def __str__(
        self: "ResultSet"
    ) -> str:
        """
        Return a compact result table.

        :return: Human-readable result summary.
        """
        if not self.results:
            return "ResultSet: No results found."
        rows = []
        for index, result in enumerate(self.results):
            similarity = (
                f"{result.similarity:.2f}"
                if result.similarity is not None
                else "N/A"
            )
            rows.append(
                f"{index:>3} | {similarity:>10} | {result.title or 'No Title'}"
            )
        header = f"{'Idx':>3} | {'Similarity':>10} | Title"
        return "\n".join(
            [
                header,
                "-" * len(header),
                *rows
            ]
        )

    def __iter__(
        self: "ResultSet"
    ) -> "ResultSet":
        """
        Reset iteration and return this collection.

        :return: Reset result iterator.
        """
        object.__setattr__(
            self,
            "index",
            0
        )
        return self

    def __next__(
        self: "ResultSet"
    ) -> Any:
        """
        Return the next result.

        :return: Next result in the collection.
        """
        if self.index < len(self.results):
            result = self.results[self.index]
            object.__setattr__(
                self,
                "index",
                self.index + 1
            )
            return result
        raise StopIteration

    def __eq__(
        self: "ResultSet",
        value: object
    ) -> bool:
        """
        Compare result payloads in order.

        :param value: Value to compare.
        :return: Whether both collections contain equal result payloads.
        """
        if not isinstance(value, ResultSet):
            return False
        return self.to_dicts() == value.to_dicts()

    def __enter__(
        self: "ResultSet"
    ) -> "ResultSet":
        """
        Enter a result-set context.

        :return: This result set.
        """
        return self

    def __getitem__(
        self: "ResultSet",
        key: Union[int, slice]
    ) -> Any:
        """
        Return a result or sliced result set.

        :param key: Integer index or slice.
        :return: Selected result or result set.
        """
        if isinstance(key, slice):
            return ResultSet(
                results=self.results[key],
                message=self.message,
                query=self.query
            )
        if not isinstance(key, int):
            raise TypeError("ResultSet indices must be integers or slices")
        try:
            return self.results[key]
        except IndexError as error:
            raise IndexError("ResultSet index out of range") from error

    def __add__(
        self: "ResultSet",
        other: Any
    ) -> "ResultSet":
        """
        Add a result or result set.

        :param other: Result or result set to append.
        :return: Combined result set.
        """
        if isinstance(other, nosible.classes.result.Result):
            return ResultSet(results=[*self.results, other])
        if isinstance(other, ResultSet):
            return ResultSet(results=self.results + other.results)
        raise TypeError("Can only add a Result or ResultSet")

    def __sub__(
        self: "ResultSet",
        other: Any
    ) -> "ResultSet":
        """
        Remove matching results.

        :param other: Result or result set to remove.
        :return: Result set without matching results.
        """
        if isinstance(other, nosible.classes.result.Result):
            removals = [other]
        elif isinstance(other, ResultSet):
            removals = other.results
        else:
            raise TypeError("Can only subtract a Result or ResultSet")
        return ResultSet(
            results=[
                result
                for result in self.results
                if result not in removals
            ]
        )

    def __del__(
        self: "ResultSet"
    ) -> None:
        """
        Release held resources.

        :return: None.
        """
        self.close()

    def find_in_search_results(
        self: "ResultSet",
        query: str,
        top_k: int = 10
    ) -> "ResultSet":
        """
        Rank existing results with an in-memory lexical index.

        :param query: Text to find within the current results.
        :param top_k: Maximum number of results to return.
        :return: Ranked result subset.
        """
        if not query.strip():
            raise ValueError("query must not be empty")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        schema_builder = SchemaBuilder()
        schema_builder.add_integer_field(
            name="doc_id",
            stored=True
        )
        schema_builder.add_text_field(
            name="content",
            stored=True
        )
        index = Index(schema=schema_builder.build())
        writer = index.writer(
            heap_size=15_000_000,
            num_threads=1
        )
        for index_value, result in enumerate(self.results):
            document = Document()
            document.add_integer(
                field_name="doc_id",
                value=index_value
            )
            document.add_text(
                field_name="content",
                value=" ".join(
                    part
                    for part in [
                        result.title or "",
                        result.description or "",
                        result.content or ""
                    ]
                    if part
                )
            )
            writer.add_document(doc=document)
        writer.commit()
        index.reload()

        searcher = index.searcher()
        parsed_query = index.parse_query(
            query=query,
            default_field_names=[
                "content"
            ]
        )
        hits = searcher.search(
            query=parsed_query,
            limit=top_k
        ).hits
        matched_indices = [
            searcher.doc(doc_address=address).get_first(fieldname="doc_id")
            for score, address in hits
        ]
        ranked_results = [
            self.results[index_value]
            for index_value in matched_indices
        ]
        if len(ranked_results) < top_k:
            for index_value, result in enumerate(self.results):
                if index_value not in matched_indices:
                    ranked_results.append(result)
                if len(ranked_results) == top_k:
                    break
        return ResultSet(results=ranked_results)

    def analyze(
        self: "ResultSet",
        by: str = "published"
    ) -> Dict[str, Any]:
        """
        Summarize a supported result field.

        :param by: Field to summarize.
        :return: Field-dependent summary.
        """
        supported_fields = {
            "netloc",
            "published",
            "visited",
            "author",
            "language",
            "similarity"
        }
        if by not in supported_fields:
            raise ValueError(f"Cannot analyze by '{by}' - not a valid field.")
        frame = self.to_polars().drop_nulls(subset=by)
        if frame.is_empty():
            return {}
        if by == "author":
            frame = frame.with_columns(
                pl.when(pl.col("author") == "")
                .then(statement=pl.lit(value="Author Unknown"))
                .otherwise(statement=pl.col("author"))
                .alias(name="author")
            )
        if by in {
            "published",
            "visited"
        }:
            return analyze_dates(
                frame=frame,
                column=by
            )
        if by == "similarity":
            return analyze_similarity(frame=frame)
        counts = frame.get_column(name=by).value_counts(sort=True)
        return {
            row[by]: row["count"]
            for row in counts.to_dicts()
        }

    def write_csv(
        self: "ResultSet",
        file_path: Optional[str] = None,
        delimiter: str = ",",
        encoding: str = "utf-8"
    ) -> str:
        """
        Write results to CSV.

        :param file_path: Optional destination path.
        :param delimiter: CSV delimiter.
        :param encoding: Text encoding.
        :return: Written file path.
        """
        output_path = os.fspath(path=file_path or "search_results.csv")
        payloads = self.to_dicts()
        serialized_payloads = [
            serialize_csv_payload(payload=payload)
            for payload in payloads
        ]
        fieldnames = csv_fieldnames(payloads=payloads)
        with open(
            file=output_path,
            mode="w",
            newline="",
            encoding=encoding
        ) as file_handle:
            writer = csv.DictWriter(
                f=file_handle,
                fieldnames=fieldnames,
                delimiter=delimiter,
                extrasaction="ignore"
            )
            writer.writeheader()
            for payload in serialized_payloads:
                writer.writerow(payload)
        return output_path

    def to_pandas(
        self: "ResultSet"
    ) -> pd.DataFrame:
        """
        Convert results to a pandas DataFrame.

        :return: pandas DataFrame.
        """
        return self.to_polars().to_pandas()

    def write_json(
        self: "ResultSet",
        file_path: Optional[str] = None
    ) -> str:
        """
        Serialize results and optionally write them to disk.

        :param file_path: Optional destination path.
        :return: File path when written, otherwise JSON text.
        """
        json_text = json_dumps(obj=self.to_dicts())
        if file_path is None:
            return json_text
        output_path = os.fspath(path=file_path)
        with open(
            file=output_path,
            mode="w",
            encoding="utf-8"
        ) as file_handle:
            file_handle.write(json_text)
        return output_path

    def to_dict(
        self: "ResultSet"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Convert results to a URL-hash-keyed dictionary.

        :return: Result payloads keyed by URL hash.
        """
        return {
            result.url_hash: result.to_dict()
            for result in self.results
            if result.url_hash
        }

    def write_ndjson(
        self: "ResultSet",
        file_path: Optional[str] = None
    ) -> str:
        """
        Serialize results as newline-delimited JSON.

        :param file_path: Optional destination path.
        :return: File path when written, otherwise NDJSON text.
        """
        ndjson_text = "".join(
            f"{json_dumps(obj=result.to_dict())}\n"
            for result in self.results
        )
        if file_path is None:
            return ndjson_text
        output_path = os.fspath(path=file_path)
        with open(
            file=output_path,
            mode="w",
            encoding="utf-8"
        ) as file_handle:
            file_handle.write(ndjson_text)
        return output_path

    def write_parquet(
        self: "ResultSet",
        file_path: Optional[str] = None
    ) -> str:
        """
        Write results to Apache Parquet.

        :param file_path: Optional destination path.
        :return: Written file path.
        """
        output_path = os.fspath(path=file_path or "results.parquet")
        self.to_polars().write_parquet(file=output_path)
        return output_path

    def write_ipc(
        self: "ResultSet",
        file_path: Optional[str] = None
    ) -> str:
        """
        Write results to Apache Arrow IPC.

        :param file_path: Optional destination path.
        :return: Written file path.
        """
        output_path = os.fspath(path=file_path or "results.arrow")
        self.to_polars().write_ipc(file=output_path)
        return output_path

    def write_duckdb(
        self: "ResultSet",
        file_path: Optional[str] = None,
        table_name: str = "results"
    ) -> str:
        """
        Write results to a DuckDB table.

        :param file_path: Optional database path.
        :param table_name: Destination table name.
        :return: Written database path.
        """
        validate_table_name(table_name=table_name)
        output_path = os.fspath(path=file_path or "results.duckdb")
        frame = self.to_polars()
        connection = duckdb.connect(database=output_path)
        try:
            connection.register(
                view_name="result_frame",
                python_object=frame
            )
            connection.execute(
                query=(
                    f'CREATE OR REPLACE TABLE "{table_name}" '
                    "AS SELECT * FROM result_frame"
                )
            )
        finally:
            connection.close()
        return output_path

    def to_polars(
        self: "ResultSet"
    ) -> pl.DataFrame:
        """
        Convert results to a Polars DataFrame.

        :return: Polars DataFrame.
        """
        return pl.DataFrame(data=self.to_dicts())

    def to_dicts(
        self: "ResultSet"
    ) -> List[Dict[str, Any]]:
        """
        Convert results to dictionaries.

        :return: Ordered result payloads.
        """
        return [
            result.to_dict()
            for result in self.results
        ]

    @classmethod
    def read_csv(
        cls: "type[ResultSet]",
        file_path: str
    ) -> "ResultSet":
        """
        Read results from CSV.

        :param file_path: Source file path.
        :return: Parsed result set.
        """
        input_path = os.fspath(path=file_path)
        with open(
            file=input_path,
            newline="",
            encoding="utf-8"
        ) as file_handle:
            reader = csv.DictReader(f=file_handle)
            fieldnames = reader.fieldnames or []
            has_metadata = any(
                field_name in fieldnames
                for field_name in {
                    CSV_PRESENT_FIELDS_COLUMN,
                    CSV_ENCODED_FIELDS_COLUMN
                }
            )
            if has_metadata:
                validate_csv_metadata(fieldnames=fieldnames)
                return cls.from_dicts(
                    dicts=[
                        deserialize_csv_payload(row=row)
                        for row in reader
                    ]
                )
        frame = pl.read_csv(source=input_path)
        return cls.from_polars(df=frame)

    @classmethod
    def read_json(
        cls: "type[ResultSet]",
        file_path: str
    ) -> "ResultSet":
        """
        Read results from JSON.

        :param file_path: Source file path.
        :return: Parsed result set.
        """
        with open(
            file=os.fspath(path=file_path),
            encoding="utf-8"
        ) as file_handle:
            data = json_loads(value=file_handle.read())
        return cls.from_dict(data=data)

    @classmethod
    def from_pandas(
        cls: "type[ResultSet]",
        df: pd.DataFrame
    ) -> "ResultSet":
        """
        Create results from a pandas DataFrame.

        :param df: Source pandas DataFrame.
        :return: Parsed result set.
        """
        return cls.from_polars(df=pl.from_pandas(data=df))

    @classmethod
    def read_ndjson(
        cls: "type[ResultSet]",
        file_path: str
    ) -> "ResultSet":
        """
        Read results from newline-delimited JSON.

        :param file_path: Source file path.
        :return: Parsed result set.
        """
        payloads = []
        with open(
            file=os.fspath(path=file_path),
            encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                if line.strip():
                    payloads.append(json_loads(value=line))
        if not payloads:
            raise ValueError("No valid search results found in the NDJSON file")
        return cls.from_dicts(dicts=payloads)

    @classmethod
    def read_parquet(
        cls: "type[ResultSet]",
        file_path: str
    ) -> "ResultSet":
        """
        Read results from Apache Parquet.

        :param file_path: Source file path.
        :return: Parsed result set.
        """
        return cls.from_polars(
            df=pl.read_parquet(source=os.fspath(path=file_path))
        )

    @classmethod
    def read_ipc(
        cls: "type[ResultSet]",
        file_path: str
    ) -> "ResultSet":
        """
        Read results from Apache Arrow IPC.

        :param file_path: Source file path.
        :return: Parsed result set.
        """
        return cls.from_polars(
            df=pl.read_ipc(source=os.fspath(path=file_path))
        )

    @classmethod
    def read_duckdb(
        cls: "type[ResultSet]",
        file_path: str
    ) -> "ResultSet":
        """
        Read results from the first DuckDB table.

        :param file_path: Source database path.
        :return: Parsed result set.
        """
        connection = duckdb.connect(
            database=os.fspath(path=file_path),
            read_only=True
        )
        try:
            tables = connection.execute(query="SHOW TABLES").fetchall()
            if not tables:
                raise ValueError("No tables found in DuckDB file")
            table_name = tables[0][0]
            validate_table_name(table_name=table_name)
            arrow_table = connection.execute(
                query=f'SELECT * FROM "{table_name}"'
            ).arrow()
        finally:
            connection.close()
        return cls.from_polars(df=pl.from_arrow(data=arrow_table))

    @classmethod
    def from_polars(
        cls: "type[ResultSet]",
        df: pl.DataFrame
    ) -> "ResultSet":
        """
        Create results from a Polars DataFrame.

        :param df: Source Polars DataFrame.
        :return: Parsed result set.
        """
        return cls.from_dicts(dicts=df.to_dicts())

    @classmethod
    def from_dict(
        cls: "type[ResultSet]",
        data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> "ResultSet":
        """
        Create results from an envelope, result dictionary, or result list.

        :param data: Search response or result payloads.
        :return: Parsed result set.
        """
        if isinstance(data, list):
            return cls.from_dicts(dicts=data)
        if not isinstance(data, dict):
            raise ValueError(
                "Input must be a list of dictionaries or a single dictionary"
            )
        if "response" not in data:
            return cls.from_dicts(dicts=[data])
        response = data.get("response")
        if not isinstance(response, list):
            raise ValueError("Search response must be a list")
        parsed = cls.from_dicts(dicts=response)
        object.__setattr__(
            parsed,
            "message",
            data.get("message")
        )
        object.__setattr__(
            parsed,
            "query",
            data.get("query")
        )
        return parsed

    @classmethod
    def from_dicts(
        cls: "type[ResultSet]",
        dicts: List[Dict[str, Any]]
    ) -> "ResultSet":
        """
        Create results from dictionaries.

        :param dicts: Search result payloads.
        :return: Parsed result set.
        """
        if not isinstance(dicts, list):
            raise ValueError("ResultSet data must be a list")
        return cls(
            results=[
                nosible.classes.result.Result.from_dict(data=data)
                for data in dicts
            ]
        )

    def close(
        self: "ResultSet"
    ) -> None:
        """
        Release held resources.

        :return: None.
        """


def csv_fieldnames(
    payloads: List[Dict[str, Any]]
) -> List[str]:
    """
    Return stable CSV fields for every known and unknown payload value.

    :param payloads: Result payloads to serialize.
    :return: Ordered CSV field names.
    """
    present_fields = {
        field_name
        for payload in payloads
        for field_name in payload
    }
    fieldnames = [
        csv_storage_field(field_name=field_name)
        for field_name in RESULT_FIELD_ORDER
        if field_name in present_fields
    ]
    known_fields = set(RESULT_FIELD_ORDER)
    for payload in payloads:
        for field_name in payload:
            if field_name in known_fields:
                continue
            fieldnames.append(
                csv_storage_field(field_name=field_name)
            )
            known_fields.update({field_name})
    fieldnames.extend(
        [
            CSV_PRESENT_FIELDS_COLUMN,
            CSV_ENCODED_FIELDS_COLUMN
        ]
    )
    return fieldnames


def serialize_csv_payload(
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Encode one result with field-presence and JSON type metadata.

    :param payload: Result payload to serialize.
    :return: Lossless CSV row.
    """
    encoded_fields = [
        field_name
        for field_name, value in payload.items()
        if value is not None
    ]
    row = {
        csv_storage_field(field_name=field_name): (
            json_dumps(obj=value)
            if field_name in encoded_fields
            else ""
        )
        for field_name, value in payload.items()
    }
    row[CSV_PRESENT_FIELDS_COLUMN] = json_dumps(obj=list(payload))
    row[CSV_ENCODED_FIELDS_COLUMN] = json_dumps(obj=encoded_fields)
    return row


def deserialize_csv_payload(
    row: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Decode one lossless CSV row to its original result payload.

    :param row: CSV row containing SDK metadata.
    :return: Restored result payload.
    """
    present_fields = json_loads(
        value=row[CSV_PRESENT_FIELDS_COLUMN]
    )
    encoded_fields = json_loads(
        value=row[CSV_ENCODED_FIELDS_COLUMN]
    )
    validate_csv_field_list(
        field_names=present_fields,
        metadata_name=CSV_PRESENT_FIELDS_COLUMN
    )
    validate_csv_field_list(
        field_names=encoded_fields,
        metadata_name=CSV_ENCODED_FIELDS_COLUMN
    )
    return {
        field_name: (
            json_loads(
                value=row[csv_storage_field(field_name=field_name)]
            )
            if field_name in encoded_fields
            else None
        )
        for field_name in present_fields
    }


def csv_storage_field(
    field_name: str
) -> str:
    """
    Escape payload headers that overlap the CSV metadata namespace.

    :param field_name: Original result field name.
    :return: Collision-safe CSV header.
    """
    if field_name in {
        CSV_PRESENT_FIELDS_COLUMN,
        CSV_ENCODED_FIELDS_COLUMN
    } or field_name.startswith(CSV_ESCAPED_FIELD_PREFIX):
        return (
            f"{CSV_ESCAPED_FIELD_PREFIX}"
            f"{json_dumps(obj=field_name)}"
        )
    return field_name


def validate_csv_metadata(
    fieldnames: List[str]
) -> None:
    """
    Require both metadata columns when either one is present.

    :param fieldnames: CSV header fields.
    :return: None.
    """
    required_fields = {
        CSV_PRESENT_FIELDS_COLUMN,
        CSV_ENCODED_FIELDS_COLUMN
    }
    if not required_fields.issubset(fieldnames):
        raise ValueError("CSV contains incomplete NOSIBLE metadata columns")


def validate_csv_field_list(
    field_names: Any,
    metadata_name: str
) -> None:
    """
    Validate decoded field-presence metadata.

    :param field_names: Decoded metadata value.
    :param metadata_name: Metadata column name.
    :return: None.
    """
    if not isinstance(field_names, list) or not all(
        isinstance(field_name, str)
        for field_name in field_names
    ):
        raise ValueError(f"Invalid CSV metadata in {metadata_name}")


def analyze_dates(
    frame: pl.DataFrame,
    column: str
) -> Dict[str, int]:
    """
    Count results by calendar month.

    :param frame: Result DataFrame.
    :param column: Date column to summarize.
    :return: Monthly counts.
    """
    normalized = frame.with_columns(
        pl.col(column)
        .cast(dtype=pl.String)
        .str.slice(
            offset=0,
            length=7
        )
        .alias(name=column)
    )
    counts = normalized.get_column(name=column).value_counts(sort=True)
    return {
        row[column]: row["count"]
        for row in counts.sort(by=column).to_dicts()
    }


def analyze_similarity(
    frame: pl.DataFrame
) -> Dict[str, Any]:
    """
    Calculate descriptive similarity statistics.

    :param frame: Result DataFrame.
    :return: Similarity statistics.
    """
    series = frame.get_column(name="similarity").cast(dtype=pl.Float64)
    return {
        "count": series.len(),
        "null_count": series.null_count(),
        "mean": series.mean(),
        "std": series.std(),
        "min": series.min(),
        "25%": series.quantile(quantile=0.25),
        "50%": series.quantile(quantile=0.50),
        "75%": series.quantile(quantile=0.75),
        "max": series.max()
    }


def validate_table_name(
    table_name: str
) -> None:
    """
    Validate a DuckDB table identifier.

    :param table_name: Table name to validate.
    :return: None.
    """
    if not SAFE_TABLE_NAME.fullmatch(string=table_name):
        raise ValueError("table_name must be a simple SQL identifier")
