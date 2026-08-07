"""Model contracts for Search API v2.1 response shapes."""

import os
from pathlib import Path
from typing import Any

import pytest

import nosible

TEST_MODULE = os.path.basename(p=__file__)


pytestmark = pytest.mark.contract


def test_fast_result_maps_nested_semantics_to_legacy_properties(
    fast_search_response: Any
) -> None:
    """

    Verify fast result maps nested semantics to legacy properties.

    :param fast_search_response: Test dependency or input.
    :return: Test result or None.
    """
    result = nosible.Result.from_dict(data=fast_search_response["response"][0])

    assert result.url_hash == "aB3dE_fG7hIj-KlMnOpQrStU"
    assert result.similarity == pytest.approx(expected=0.9123)
    assert result.best_chunk == (
        "Manufacturers are diversifying advanced chip capacity."
    )
    assert result.semantics["similarity"] == pytest.approx(expected=0.9123)
    assert result.semantics["origin_shard"] == 143
    assert result.extra["future_search_field"] == {"kept": True}


def test_fast_result_round_trip_does_not_discard_new_or_unknown_fields(
    fast_search_response: Any
) -> None:
    """

    Verify fast result round trip does not discard new or unknown fields.

    :param fast_search_response: Test dependency or input.
    :return: Test result or None.
    """
    payload = fast_search_response["response"][0]

    restored = nosible.Result.from_dict(data=payload).to_dict()

    assert restored["semantics"] == payload["semantics"]
    assert restored["best_chunk"] == payload["best_chunk"]
    assert restored["content"] == payload["content"]
    assert restored["future_search_field"] == payload["future_search_field"]


@pytest.mark.parametrize(
    argnames="payload",
    argvalues=[
        {
            "url": "https://example.com/null-semantics",
            "semantics": None
        },
        {
            "url": "https://example.com/null-similarity",
            "similarity": None,
            "semantics": {"similarity": 0.9}
        },
        {
            "url": "https://example.com/null-best-chunk",
            "best_chunk": None,
            "semantics": {"best_chunk": "derived"}
        }
    ]
)
def test_fast_result_round_trip_preserves_explicit_null_precedence(
    payload: dict[str, Any]
) -> None:
    """
    Verify explicit null Fast Search fields override derived semantics.

    :param payload: Sparse Fast Search result payload.
    :return: None.
    """
    restored = nosible.Result.from_dict(data=payload).to_dict()

    assert restored == payload


def test_result_still_accepts_the_legacy_flat_shape() -> None:
    """

    Verify result still accepts the legacy flat shape.

    :return: Test result or None.
    """
    payload = {
        "url": "https://example.com/legacy",
        "title": "Legacy result",
        "best_chunk": "Legacy best chunk.",
        "similarity": 0.77,
        "url_hash": "legacy-hash",
    }

    result = nosible.Result.from_dict(data=payload)

    assert result.title == "Legacy result"
    assert result.similarity == pytest.approx(expected=0.77)
    assert result.best_chunk == "Legacy best chunk."


def test_result_set_accepts_api_envelope_and_preserves_response_metadata(
    fast_search_response: Any
) -> None:
    """

    Verify result set accepts api envelope and preserves response metadata.

    :param fast_search_response: Test dependency or input.
    :return: Test result or None.
    """
    result_set = nosible.ResultSet.from_dict(data=fast_search_response)

    assert len(result_set) == 1
    assert result_set.message == "Search completed."
    assert result_set.query == fast_search_response["query"]
    assert result_set[0].similarity == pytest.approx(expected=0.9123)


def test_result_set_csv_round_trip_preserves_current_and_sparse_payloads(
    tmp_path: Path,
    fast_search_response: Any
) -> None:
    """
    Verify CSV retains nested, unknown, null, omitted, and scalar values.

    :param tmp_path: Temporary test directory.
    :param fast_search_response: Representative Fast Search response.
    :return: None.
    """
    payloads = [
        fast_search_response["response"][0],
        {
            "url": "https://example.com/sparse",
            "title": "",
            "similarity": None,
            "future_bool": False,
            "future_count": 0,
            "future_list": [
                "value",
                None
            ],
            "__nosible_present_fields__": "preserved user field",
            "__nosible_escaped_field__custom": {
                "preserved": True
            }
        }
    ]
    result_set = nosible.ResultSet.from_dicts(dicts=payloads)
    csv_path = tmp_path / "results.csv"

    result_set.write_csv(file_path=csv_path)
    restored = nosible.ResultSet.read_csv(file_path=csv_path)

    assert restored.to_dicts() == payloads


def test_result_set_reads_legacy_csv_without_sdk_metadata(
    tmp_path: Path
) -> None:
    """
    Verify CSV files created before the lossless format remain readable.

    :param tmp_path: Temporary test directory.
    :return: None.
    """
    csv_path = tmp_path / "legacy.csv"
    csv_path.write_text(
        data=(
            "url,title,similarity\n"
            "https://example.com,Example,0.5\n"
        ),
        encoding="utf-8"
    )

    restored = nosible.ResultSet.read_csv(file_path=csv_path)

    assert restored[0].url == "https://example.com"
    assert restored[0].title == "Example"
    assert restored[0].similarity == pytest.approx(expected=0.5)


def test_rich_result_preserves_each_enrichment_block(
    rich_search_response: Any
) -> None:
    """

    Verify rich result preserves each enrichment block.

    :param rich_search_response: Test dependency or input.
    :return: Test result or None.
    """
    result = nosible.RichResult.from_dict(data=rich_search_response["response"][0])

    assert result.page["url_hash"] == "aB3dE_fG7hIj-KlMnOpQrStU"
    assert result.snippet["best_chunk"].startswith("Manufacturers")
    assert result.tokens["content"].startswith("manufacturers")
    assert result.similarity == pytest.approx(expected=0.9345)
    assert result.profile["legal_name"] == "Example News Ltd"
    assert result.targeting["brand_safety"] == "Safe"
    assert result.history["first_published"] == "2024-01-01"
    assert result.signals["prob_positive"] == pytest.approx(expected=0.81)
    assert result.vectors["nosible_bitstring"] == "kK9mQ2xZvB4w=="
    assert result.extra["future_rich_field"] == "must survive"


def test_rich_result_round_trip_is_lossless(
    rich_search_response: Any
) -> None:
    """

    Verify rich result round trip is lossless.

    :param rich_search_response: Test dependency or input.
    :return: Test result or None.
    """
    payload = rich_search_response["response"][0]

    restored = nosible.RichResult.from_dict(data=payload).to_dict()

    assert restored == payload


def test_rich_result_preserves_explicit_nullable_enrichment_blocks(
    rich_search_response: Any
) -> None:
    """

    Verify rich result preserves explicit nullable enrichment blocks.

    :param rich_search_response: Test dependency or input.
    :return: Test result or None.
    """
    payload = rich_search_response["response"][0]
    payload["signals"] = None
    payload["vectors"] = None

    restored = nosible.RichResult.from_dict(data=payload).to_dict()

    assert restored == payload


def test_rich_result_preserves_explicit_nullable_core_blocks() -> None:
    """
    Verify explicit null core Rich Search blocks remain null.

    :return: None.
    """
    payload = {
        "page": None,
        "snippet": None,
        "tokens": None,
        "semantics": None
    }

    result = nosible.RichResult.from_dict(data=payload)

    assert result.to_dict() == payload
    assert result.similarity is None


def test_sparse_snippet_round_trip_preserves_omitted_fields() -> None:
    """
    Verify sparse snippets do not grow absent fields during round trips.

    :return: None.
    """
    payload = {
        "content": "Sparse snippet.",
        "future_snippet_field": {"kept": True}
    }

    restored = nosible.Snippet.from_dict(data=payload).to_dict()

    assert restored == payload


def test_sparse_snippet_round_trip_preserves_explicit_nulls() -> None:
    """
    Verify sparse snippets distinguish explicit nulls from omitted fields.

    :return: None.
    """
    payload = {
        "content": None,
        "snippet_hash": "snippet-1"
    }

    restored = nosible.Snippet.from_dict(data=payload).to_dict()

    assert restored == payload


def test_empty_snippet_round_trip_stays_empty() -> None:
    """
    Verify an empty wire snippet does not acquire default-valued fields.

    :return: None.
    """
    assert nosible.Snippet.from_dict(data={}).to_dict() == {}
