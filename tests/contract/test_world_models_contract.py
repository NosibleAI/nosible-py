"""Model contracts derived from the World v1.2 event emitter and dictionary."""

import os
from typing import Any

import pytest

import nosible

TEST_MODULE = os.path.basename(p=__file__)


pytestmark = pytest.mark.contract


ONTOLOGY_FAMILIES = {
    "iptc_genre",
    "media_frame",
    "iptc_media_topics",
    "iab",
    "ekman7_emotion",
    "schema_org_event",
    "gics",
    "mitre_attack",
    "emdat",
    "plover",
    "icd11",
    "sportsml",
    "nosible",
    "asset_class",
    "sdgs",
}


def test_world_event_v1_2_core_fields(
    world_event_data: Any
) -> None:
    """

    Verify world event v1 2 core fields.

    :param world_event_data: Test dependency or input.
    :return: Test result or None.
    """
    event = nosible.WorldEvent.from_dict(data=world_event_data)

    assert event.event_id == world_event_data["event_id"]
    assert event.version == "1.2"
    assert event.has_tickers is True
    assert event.event["title"] == (
        "Chipmakers expand advanced packaging capacity"
    )
    assert event.signals["materiality"] == "high"
    assert event.coverage["total_coverage"] == 128
    assert event.coordinate["source"] == "primary_location"
    assert event.tickers[0]["ticker_serp"] == "NVDA.US"
    assert len(event.event_id) == 72
    assert event.event_id.split(sep="_")[3] == "v1"


def test_world_event_preserves_ranked_ontology_candidates(
    world_event_data: Any
) -> None:
    """

    Verify world event preserves ranked ontology candidates.

    :param world_event_data: Test dependency or input.
    :return: Test result or None.
    """
    event = nosible.WorldEvent.from_dict(data=world_event_data)

    assert set(event.ontology) >= ONTOLOGY_FAMILIES
    assert len(event.ontology["iptc_media_topics"]) == 2
    assert event.ontology["iptc_media_topics"][0]["level_3"] == "semiconductors"
    assert event.ontology["gics"][0]["cosine"] == pytest.approx(expected=0.94)
    assert event.ontology["mitre_attack"][0]["below_floor"] is True


def test_world_event_preserves_arbitrary_ner_and_future_ontology_types(
    world_event_data: Any
) -> None:
    """

    Verify world event preserves arbitrary ner and future ontology types.

    :param world_event_data: Test dependency or input.
    :return: Test result or None.
    """
    event = nosible.WorldEvent.from_dict(data=world_event_data)

    assert event.entities["FUTURE_NER_TYPE"] == {"Preserve Me": 1}
    assert event.ontology["future_ontology"][0]["label"] == (
        "Preserve new taxonomies"
    )


def test_world_event_preserves_provenance_timestamps_and_vectors(
    world_event_data: Any
) -> None:
    """

    Verify world event preserves provenance timestamps and vectors.

    :param world_event_data: Test dependency or input.
    :return: Test result or None.
    """
    event = nosible.WorldEvent.from_dict(data=world_event_data)

    assert [item["event_score"] for item in event.provenance] == [0.982, 0.911]
    assert event.timestamps["first_seen"] == "2026-07-20T08:30:00Z"
    assert event.timestamps["hourly_counts_utc"]["2026-07-20T09:00:00Z"] == 23
    assert event.similar
    assert all(len(event_id) == 72 for event_id in event.similar)
    assert all(
        event_id.split(sep="_")[3] == "v1"
        for event_id in event.similar
    )
    assert event.oai_vector == "0.012,-0.034,0.056"


def test_world_event_probability_blocks_remain_available(
    world_event_data: Any
) -> None:
    """

    Verify world event probability blocks remain available.

    :param world_event_data: Test dependency or input.
    :return: Test result or None.
    """
    event = nosible.WorldEvent.from_dict(data=world_event_data)
    probabilities = event.extra["signals"]

    assert sum(probabilities["sentiment"].values()) == pytest.approx(expected=1.0)
    assert sum(probabilities["forward_looking"].values()) == pytest.approx(expected=1.0)


def test_world_event_round_trip_is_lossless_for_schema_evolution(
    world_event_data: Any
) -> None:
    """

    Verify world event round trip is lossless for schema evolution.

    :param world_event_data: Test dependency or input.
    :return: Test result or None.
    """
    restored = nosible.WorldEvent.from_dict(data=world_event_data).to_dict()

    assert restored == world_event_data
    assert restored["future_top_level_field"] == {"kept": True}


def test_world_event_allows_nullable_optional_blocks(
    world_event_data: Any
) -> None:
    """

    Verify world event allows nullable optional blocks.

    :param world_event_data: Test dependency or input.
    :return: Test result or None.
    """
    world_event_data["coordinate"] = None
    world_event_data["tickers"] = []
    world_event_data["has_tickers"] = False
    world_event_data["oai_vector"] = None

    event = nosible.WorldEvent.from_dict(data=world_event_data)

    assert event.coordinate is None
    assert event.tickers == []
    assert event.has_tickers is False
    assert event.oai_vector is None


def test_world_event_round_trip_preserves_explicit_null_core_mappings() -> None:
    """
    Verify explicit null core mappings remain null during round trips.

    :return: None.
    """
    payload = {
        "event_id": "event-null",
        "event": None,
        "signals": None,
        "coverage": None,
        "entities": None,
        "ontology": None
    }

    restored = nosible.WorldEvent.from_dict(data=payload).to_dict()

    assert restored == payload


def test_world_event_lite_projection_round_trips_without_inventing_fields(
    world_event_data: Any
) -> None:
    """

    Verify world event lite projection round trips without inventing fields.

    :param world_event_data: Test dependency or input.
    :return: Test result or None.
    """
    lite = {
        key: world_event_data[key]
        for key in (
            "event_id",
            "has_tickers",
            "event",
            "coordinate",
            "signals",
            "coverage",
        )
    }

    event = nosible.WorldEvent.from_dict(data=lite)

    assert event.event_id == world_event_data["event_id"]
    assert event.entities == {}
    assert event.to_dict() == lite


def test_world_event_keeps_legacy_single_ontology_and_provenance_map_shapes(
    world_event_data: Any
) -> None:
    """

    Verify world event keeps legacy single ontology and provenance map shapes.

    :param world_event_data: Test dependency or input.
    :return: Test result or None.
    """
    world_event_data["ontology"]["gics"] = world_event_data["ontology"]["gics"][0]
    world_event_data["provenance"] = {
        "en": world_event_data["provenance"],
    }

    restored = nosible.WorldEvent.from_dict(data=world_event_data).to_dict()

    assert restored["ontology"]["gics"]["sector"] == "Information Technology"
    assert restored["provenance"]["en"][0]["language"] == "en"


def test_world_event_page_behaves_like_existing_collection_models(
    world_event_page_data: Any
) -> None:
    """

    Verify world event page behaves like existing collection models.

    :param world_event_page_data: Test dependency or input.
    :return: Test result or None.
    """
    page = nosible.WorldEventPage.from_dict(data=world_event_page_data)

    assert len(page) == 1
    assert page[0].event_id == world_event_page_data["events"][0]["event_id"]
    assert [event.event_id for event in page] == [page[0].event_id]
    assert page.total == 1
    assert page.count == 1
    assert page.next_cursor == "cursor-next"
    assert page.facets == {}


def test_world_event_page_accepts_bare_event_lists(
    world_event_data: Any
) -> None:
    """

    Verify world event page accepts bare event lists.

    :param world_event_data: Test dependency or input.
    :return: Test result or None.
    """
    page = nosible.WorldEventPage.from_dict(data=[world_event_data])

    assert len(page) == 1
    assert page.total == 1
    assert page.count == 1


def test_world_event_page_round_trip_keeps_pagination_and_facets(
    world_event_page_data: Any
) -> None:
    """

    Verify world event page round trip keeps pagination and facets.

    :param world_event_page_data: Test dependency or input.
    :return: Test result or None.
    """
    page = nosible.WorldEventPage.from_dict(data=world_event_page_data)

    assert page.to_dict() == world_event_page_data


def test_world_event_page_round_trip_preserves_response_envelope(
    world_event_data: Any
) -> None:
    """
    Verify response envelopes do not acquire a duplicate events field.

    :param world_event_data: Representative World event payload.
    :return: None.
    """
    payload = {
        "response": [world_event_data],
        "count": 1
    }

    restored = nosible.WorldEventPage.from_dict(data=payload).to_dict()

    assert restored == payload


@pytest.mark.parametrize(
    argnames="metadata_key,metadata_value",
    argvalues=[
        ("events_field", "hijack"),
        ("bare", True),
        ("metadata", {"x": 1})
    ]
)
def test_world_event_page_unknown_metadata_cannot_overwrite_internal_state(
    world_event_data: Any,
    metadata_key: str,
    metadata_value: Any
) -> None:
    """
    Verify arbitrary metadata keys round-trip without changing page state.

    :param world_event_data: Representative World event payload.
    :param metadata_key: Metadata key that collides with internal state.
    :param metadata_value: Metadata value to preserve.
    :return: None.
    """
    payload = {
        "response": [world_event_data],
        metadata_key: metadata_value
    }

    restored = nosible.WorldEventPage.from_dict(data=payload).to_dict()

    assert restored == payload
