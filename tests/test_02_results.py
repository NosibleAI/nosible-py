"""Tests for test 02 results."""

import os
from typing import Any

import pandas as pd
import pytest

from nosible import Nosible, Result, ResultSet

TEST_MODULE = os.path.basename(p=__file__)


def test_resultset_type(
    search_data: Any
) -> None:
    """

    Verify resultset type.

    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    assert isinstance(search_data, ResultSet)


def test_resultset_iterable(
    search_data: Any
) -> None:
    """

    Verify resultset iterable.

    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    assert all(isinstance(res, Result) for res in search_data)


def test_result_access_and_types(
    search_data: Any
) -> None:
    """

    Verify result access and types.

    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    result = search_data[0]
    assert isinstance(result, Result)
    assert isinstance(result.url, str)
    assert isinstance(result.title, str)
    assert isinstance(result.content, str)
    assert isinstance(result.language, str)
    assert isinstance(result.netloc, str)
    assert isinstance(result.published, str)
    assert isinstance(result.similarity, float)
    assert isinstance(result.title, str)


def test_resultset_addition_and_equality(
    search_data: Any
) -> None:
    """

    Verify resultset addition and equality.

    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    first_result = search_data[1]
    second_result = search_data[2]
    combined_results = first_result + second_result
    assert isinstance(combined_results, ResultSet)
    assert first_result == Result.from_dict(data=first_result.to_dict())

    third_result = search_data[3]
    expanded_results = combined_results + third_result
    assert isinstance(expanded_results, ResultSet)


def test_resultset_json_io(
    tmp_path: Any,
    search_data: Any
) -> None:
    """

    Verify resultset json io.

    :param tmp_path: Test dependency or input.
    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    search_data.write_json(file_path=tmp_path / "results_copy.json")
    results_copy = ResultSet.read_json(file_path=tmp_path / "results_copy.json")
    assert search_data == results_copy
    assert len(search_data) == len(results_copy)


def test_resultset_csv_io(
    tmp_path: Any,
    search_data: Any
) -> None:
    """

    Verify resultset csv io.

    :param tmp_path: Test dependency or input.
    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    search_data.write_csv(file_path=tmp_path / "results_copy.csv")
    results_copy_csv = ResultSet.read_csv(file_path=tmp_path / "results_copy.csv")
    assert search_data == results_copy_csv
    assert len(search_data) == len(results_copy_csv)


def test_resultset_parquet_io(
    tmp_path: Any,
    search_data: Any
) -> None:
    """

    Verify resultset parquet io.

    :param tmp_path: Test dependency or input.
    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    search_data.write_parquet(file_path=tmp_path / "results_copy.parquet")
    results_copy_parquet = ResultSet.read_parquet(file_path=tmp_path / "results_copy.parquet")
    assert search_data == results_copy_parquet
    assert len(search_data) == len(results_copy_parquet)


def test_resultset_arrow_io(
    tmp_path: Any,
    search_data: Any
) -> None:
    """

    Verify resultset arrow io.

    :param tmp_path: Test dependency or input.
    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    search_data.write_ipc(file_path=tmp_path / "results_copy.ipc")
    results_copy_arrow = ResultSet.read_ipc(file_path=tmp_path / "results_copy.ipc")
    assert search_data == results_copy_arrow
    assert len(search_data) == len(results_copy_arrow)


def test_resultset_polars(
    search_data: Any
) -> None:
    """

    Verify resultset polars.

    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    pol = search_data.to_polars()
    results_copy_polars = ResultSet.from_polars(df=pol)
    assert search_data == results_copy_polars


def test_resultset_to_dict(
    search_data: Any
) -> None:
    """

    Verify resultset to dict.

    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    results_dict = search_data.to_dict()
    assert isinstance(results_dict, dict)
    for key, result_payload in results_dict.items():
        assert isinstance(result_payload, dict)
        assert "url" in result_payload
        assert "title" in result_payload
        assert "content" in result_payload
        assert "language" in result_payload
        assert "netloc" in result_payload
        assert "published" in result_payload
        assert "similarity" in result_payload
        assert result_payload["url_hash"] == key


def test_resultset_to_dicts(
    search_data: Any
) -> None:
    """

    Verify resultset to dicts.

    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    results_dicts = search_data.to_dicts()
    assert isinstance(results_dicts, list)
    for result_payload in results_dicts:
        assert isinstance(result_payload, dict)
        assert "url" in result_payload
        assert "title" in result_payload
        assert "content" in result_payload
        assert "language" in result_payload
        assert "netloc" in result_payload
        assert "published" in result_payload
        assert "similarity" in result_payload
        assert "url_hash" in result_payload


def test_resultset_write_ndjson(
    tmp_path: Any,
    search_data: Any
) -> None:
    """

    Verify resultset write ndjson.

    :param tmp_path: Test dependency or input.
    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    search_data.write_ndjson(file_path=tmp_path / "results_copy.ndjson")
    results_copy_ndjson = ResultSet.read_ndjson(file_path=tmp_path / "results_copy.ndjson")
    assert search_data == results_copy_ndjson
    assert len(search_data) == len(results_copy_ndjson)


def test_resultset_to_pandas(
    search_data: Any
) -> None:
    """

    Verify resultset to pandas.

    :param search_data: Test dependency or input.
    :return: Test result or None.
    """
    frame = search_data.to_pandas()
    results_copy_pandas = ResultSet.from_pandas(df=frame)
    assert search_data == results_copy_pandas
    assert len(search_data) == len(results_copy_pandas)
    assert isinstance(frame, pd.DataFrame)
    assert "url" in frame.columns
    assert "title" in frame.columns
    assert "content" in frame.columns
    assert "language" in frame.columns
    assert "netloc" in frame.columns
    assert "published" in frame.columns
    assert "similarity" in frame.columns


def test_resultset_getitem(
    search_data: Any
) -> None:
    """
    Verify integer and slice access for a result set.

    :param search_data: Live search result set.
    :return: None.
    """
    assert isinstance(search_data[0], Result)
    assert isinstance(search_data[1:3], ResultSet)

    with pytest.raises(expected_exception=IndexError):
        _ = search_data[len(search_data)]
    with pytest.raises(expected_exception=TypeError):
        _ = search_data["invalid"]


def test_similar_excludes_current_document() -> None:
    """
    Verify that similarity search excludes its source document.

    :return: None.
    """
    with Nosible(concurrency=1) as nos:
        search_results = nos.fast_search(
            question="Hedge funds seek to expand into private credit",
            n_results=10
        )
        first_result = search_results[0]
        similar_results = first_result.similar(
            client=nos,
            n_results=10
        )

        similar_hashes = [result.url_hash for result in similar_results if result.url_hash]
        assert first_result.url_hash not in similar_hashes, (
            f"Original result URL hash {first_result.url_hash} "
            "should not be in similar results"
        )

        assert len(similar_results) > 0, "Similar results should be returned"
