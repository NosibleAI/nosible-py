import tempfile
import pandas as pd
import polars as pl
import pytest

from nosible import ResultSet, Result

@pytest.fixture
def simple_results():
    return [
        Result(url="https://example.com", title="Example Domain"),
        Result(url="https://openai.com", title="OpenAI"),
    ]

def test_csv_polars_pandas_json_ndjson_parquet_arrow_duckdb_io(tmp_path, simple_results):
    rs = ResultSet(simple_results)

    # CSV
    csv_path = tmp_path / "r.csv"
    out = rs.to_csv(csv_path)
    assert str(out).endswith(".csv")
    assert rs == ResultSet.from_csv(csv_path)

    # Polars
    dfp = pl.DataFrame([r.to_dict() for r in simple_results])
    rs_from_pl = ResultSet.from_polars(dfp)
    assert len(rs_from_pl) == 2

    # Arrow
    ipc_path = tmp_path / "r.ipc"
    assert str(rs.to_arrow(ipc_path)).endswith(".ipc")
    assert rs == ResultSet.from_arrow(ipc_path)

    # Parquet
    pq_path = tmp_path / "r.parquet"
    assert str(rs.to_parquet(pq_path)).endswith(".parquet")
    assert rs == ResultSet.from_parquet(pq_path)

    # JSON
    json_path = tmp_path / "r.json"
    assert str(rs.to_json(file_path=json_path)).endswith(".json")
    assert rs == ResultSet.from_json(json_path)

    # NDJSON
    ndj_path = tmp_path / "r.ndjson"
    assert str(rs.to_ndjson(file_path=ndj_path)).endswith(".ndjson")
    assert rs == ResultSet.from_ndjson(ndj_path)

    # dicts
    dicts = rs.to_dicts()
    assert isinstance(dicts, list)
    assert isinstance(dicts[0], dict)
    assert rs == ResultSet.from_dicts(dicts)

    # single dict
    single = {"url": "https://x", "url_hash": "h1", "title": "X"}
    rs_single = ResultSet.from_dict(single)
    assert len(rs_single) == 1
    rs_list = ResultSet.from_dict(dicts)
    assert len(rs_list) == 2

    # DuckDB
    db_path = tmp_path / "r.duckdb"
    assert str(rs.to_duckdb(file_path=db_path, table_name="t")).endswith(".duckdb")
    assert rs == ResultSet.from_duckdb(db_path)
