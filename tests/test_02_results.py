import pytest
from polars.dependencies import pandas as pd
from nosible import Result, ResultSet


def test_resultset_type(search_data):
    assert isinstance(search_data, ResultSet)


def test_resultset_iterable(search_data):
    assert all(isinstance(res, Result) for res in search_data)


def test_result_access_and_types(search_data):
    r = search_data[0]
    assert isinstance(r, Result)
    assert isinstance(r.url, str)
    assert isinstance(r.title, str)
    assert isinstance(r.content, str)
    assert isinstance(r.language, str)
    assert isinstance(r.netloc, str)
    assert isinstance(r.published, str)
    assert isinstance(r.similarity, float)
    assert isinstance(r.title, str)


def test_resultset_addition_and_equality(search_data):
    r1 = search_data[1]
    r2 = search_data[2]
    a = r1 + r2
    assert isinstance(a, ResultSet)
    assert r1 == Result.from_dict(r1.to_dict())

    # add 1 result to the resultset
    r3 = search_data[3]
    b = a + r3
    assert isinstance(b, ResultSet)


def test_resultset_json_io(tmp_path, search_data):
    search_data.to_json(tmp_path / "results_copy.json")
    results_copy = ResultSet.from_json(tmp_path / "results_copy.json")
    assert search_data == results_copy
    assert len(search_data) == len(results_copy)


def test_resultset_csv_io(tmp_path, search_data):
    search_data.to_csv(tmp_path / "results_copy.csv")
    results_copy_csv = ResultSet.from_csv(tmp_path / "results_copy.csv")
    assert search_data == results_copy_csv
    assert len(search_data) == len(results_copy_csv)


def test_resultset_parquet_io(tmp_path, search_data):
    search_data.to_parquet(tmp_path / "results_copy.parquet")
    results_copy_parquet = ResultSet.from_parquet(tmp_path / "results_copy.parquet")
    assert search_data == results_copy_parquet
    assert len(search_data) == len(results_copy_parquet)


def test_resultset_arrow_io(tmp_path, search_data):
    search_data.to_arrow(tmp_path / "results_copy.ipc")
    results_copy_arrow = ResultSet.from_arrow(tmp_path / "results_copy.ipc")
    assert search_data == results_copy_arrow
    assert len(search_data) == len(results_copy_arrow)


def test_resultset_polars(search_data):
    pol = search_data.to_polars()
    results_copy_polars = ResultSet.from_polars(pol)
    assert search_data == results_copy_polars


def test_resultset_to_dict(search_data):
    results_dict = search_data.to_dict()
    assert isinstance(results_dict, dict)
    for key, res in results_dict.items():
        assert isinstance(res, dict)
        assert "url" in res
        assert "title" in res
        assert "content" in res
        assert "language" in res
        assert "netloc" in res
        assert "published" in res
        assert "similarity" in res
        assert res["url_hash"] == key
    # results_copy_from_dict = ResultSet.from_dict(results_dict)
    # assert results == results_copy_from_dict


# to_dicts
def test_resultset_to_dicts(search_data):
    results_dicts = search_data.to_dicts()
    assert isinstance(results_dicts, list)
    for res in results_dicts:
        assert isinstance(res, dict)
        assert "url" in res
        assert "title" in res
        assert "content" in res
        assert "language" in res
        assert "netloc" in res
        assert "published" in res
        assert "similarity" in res
        assert "url_hash" in res


# ndjson
def test_resultset_to_ndjson(tmp_path, search_data):
    search_data.to_ndjson(tmp_path / "results_copy.ndjson")
    results_copy_ndjson = ResultSet.from_ndjson(tmp_path / "results_copy.ndjson")
    assert search_data == results_copy_ndjson
    assert len(search_data) == len(results_copy_ndjson)


# to_pandas
def test_resultset_to_pandas(search_data):
    df = search_data.to_pandas()
    results_copy_pandas = ResultSet.from_pandas(df)
    assert search_data == results_copy_pandas
    assert len(search_data) == len(results_copy_pandas)
    assert isinstance(df, pd.DataFrame)
    assert "url" in df.columns
    assert "title" in df.columns
    assert "content" in df.columns
    assert "language" in df.columns
    assert "netloc" in df.columns
    assert "published" in df.columns
    assert "similarity" in df.columns


def test_resultset_getitem(search_data):
    """
    Test the __getitem__ method of ResultSet.

    This test checks if the ResultSet can be indexed with an integer or a slice,
    and if it raises an IndexError for out-of-range indices.

    Raises
    ------
    TypeError
        If the key is not an integer or a slice.
    IndexError
        If the index is out of range.
    """
    assert isinstance(search_data[0], Result)
    assert isinstance(search_data[1:3], ResultSet)

    with pytest.raises(IndexError):
        _ = search_data[len(search_data)]  # Out of range index
    with pytest.raises(TypeError):
        _ = search_data["invalid"]  # Invalid type for index
