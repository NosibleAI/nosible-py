"""Tests for test io formats."""

import os
from typing import Any

import polars as pl
import pytest

from nosible import Result, ResultSet

TEST_MODULE = os.path.basename(p=__file__)


@pytest.fixture
def simple_results() -> Any:
    """

    Provide simple results.

    :return: Test result or None.
    """
    return [Result(
        url="https://example.com",
        title="Example Domain"
    ), Result(
        url="https://openai.com",
        title="OpenAI"
    )]


def test_csv_polars_pandas_json_ndjson_parquet_arrow_duckdb_io(
    tmp_path: Any,
    simple_results: Any
) -> None:
    """

    Verify csv polars pandas json ndjson parquet arrow duckdb io.

    :param tmp_path: Test dependency or input.
    :param simple_results: Test dependency or input.
    :return: Test result or None.
    """
    result_set = ResultSet(results=simple_results)

    csv_path = tmp_path / "r.csv"
    written_path = result_set.write_csv(file_path=csv_path)
    assert str(written_path).endswith(".csv")
    assert result_set == ResultSet.read_csv(file_path=csv_path)

    frame = pl.DataFrame(data=[result.to_dict() for result in simple_results])
    polars_results = ResultSet.from_polars(df=frame)
    assert len(polars_results) == 2

    ipc_path = tmp_path / "r.ipc"
    assert str(result_set.write_ipc(file_path=ipc_path)).endswith(".ipc")
    assert result_set == ResultSet.read_ipc(file_path=ipc_path)

    parquet_path = tmp_path / "r.parquet"
    assert str(result_set.write_parquet(file_path=parquet_path)).endswith(".parquet")
    assert result_set == ResultSet.read_parquet(file_path=parquet_path)

    json_path = tmp_path / "r.json"
    assert str(result_set.write_json(file_path=json_path)).endswith(".json")
    assert result_set == ResultSet.read_json(file_path=json_path)

    ndjson_path = tmp_path / "r.ndjson"
    assert str(result_set.write_ndjson(file_path=ndjson_path)).endswith(".ndjson")
    assert result_set == ResultSet.read_ndjson(file_path=ndjson_path)

    dicts = result_set.to_dicts()
    assert isinstance(dicts, list)
    assert isinstance(dicts[0], dict)
    assert result_set == ResultSet.from_dicts(dicts=dicts)

    single = {"url": "https://x", "url_hash": "h1", "title": "X"}
    single_result_set = ResultSet.from_dict(data=single)
    assert len(single_result_set) == 1
    list_result_set = ResultSet.from_dict(data=dicts)
    assert len(list_result_set) == 2

    database_path = tmp_path / "r.duckdb"
    assert str(result_set.write_duckdb(
        file_path=database_path,
        table_name="t"
    )).endswith(".duckdb")
    assert result_set == ResultSet.read_duckdb(file_path=database_path)
