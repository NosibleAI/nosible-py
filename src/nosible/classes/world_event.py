"""Lossless models for NOSIBLE World event payloads."""

import os
import copy
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Set, Union

MODULE_NAME = os.path.basename(p=__file__)
WORLD_EVENT_FIELDS: Set[str] = {
    "event_id",
    "version",
    "has_tickers",
    "event",
    "coordinate",
    "signals",
    "coverage",
    "entities",
    "tickers",
    "ontology",
    "provenance",
    "timestamps",
    "similar",
    "oai_vector",
    "extra"
}


@dataclass
class WorldEvent:
    """A World v1.2 event or a compatible lite projection."""

    event_id: Optional[str] = None
    version: Optional[str] = None
    has_tickers: Optional[bool] = None
    event: Optional[Dict[str, Any]] = field(default_factory=dict)
    coordinate: Optional[Dict[str, Any]] = None
    signals: Optional[Dict[str, Any]] = field(default_factory=dict)
    coverage: Optional[Dict[str, Any]] = field(default_factory=dict)
    entities: Optional[Dict[str, Any]] = field(default_factory=dict)
    tickers: Optional[List[Any]] = field(default_factory=list)
    ontology: Optional[Dict[str, Any]] = field(default_factory=dict)
    provenance: Any = field(default_factory=list)
    timestamps: Optional[Dict[str, Any]] = field(default_factory=dict)
    similar: Optional[Dict[str, Any]] = field(default_factory=dict)
    oai_vector: Any = None
    extra: Optional[Dict[str, Any]] = field(default_factory=dict)
    unknown_fields: Dict[str, Any] = field(
        default_factory=dict,
        repr=False
    )
    present_fields: Set[str] = field(
        default_factory=set,
        repr=False
    )

    @classmethod
    def from_dict(
        cls: "type[WorldEvent]",
        data: Dict[str, Any]
    ) -> "WorldEvent":
        """
        Create a World event without discarding unknown response fields.

        :param data: World event payload.
        :return: Parsed World event.
        """
        if not isinstance(data, dict):
            raise ValueError(
                f"{MODULE_NAME}: WorldEvent data must be a dictionary"
            )

        return cls(
            event_id=data.get("event_id"),
            version=data.get("version"),
            has_tickers=data.get("has_tickers"),
            event=(
                copy.deepcopy(x=data["event"])
                if "event" in data
                else {}
            ),
            coordinate=copy.deepcopy(x=data.get("coordinate")),
            signals=(
                copy.deepcopy(x=data["signals"])
                if "signals" in data
                else {}
            ),
            coverage=(
                copy.deepcopy(x=data["coverage"])
                if "coverage" in data
                else {}
            ),
            entities=(
                copy.deepcopy(x=data["entities"])
                if "entities" in data
                else {}
            ),
            tickers=(
                copy.deepcopy(x=data["tickers"])
                if "tickers" in data
                else []
            ),
            ontology=(
                copy.deepcopy(x=data["ontology"])
                if "ontology" in data
                else {}
            ),
            provenance=(
                copy.deepcopy(x=data["provenance"])
                if "provenance" in data
                else []
            ),
            timestamps=(
                copy.deepcopy(x=data["timestamps"])
                if "timestamps" in data
                else {}
            ),
            similar=(
                copy.deepcopy(x=data["similar"])
                if "similar" in data
                else {}
            ),
            oai_vector=copy.deepcopy(x=data.get("oai_vector")),
            extra=(
                copy.deepcopy(x=data["extra"])
                if "extra" in data
                else {}
            ),
            unknown_fields={
                key: copy.deepcopy(x=value)
                for key, value in data.items()
                if key not in WORLD_EVENT_FIELDS
            },
            present_fields=set(data)
        )

    def to_dict(
        self: "WorldEvent"
    ) -> Dict[str, Any]:
        """
        Convert the event to its lossless dictionary representation.

        :return: World event payload.
        """
        data = copy.deepcopy(x=self.unknown_fields)
        known_values = {
            "event_id": self.event_id,
            "version": self.version,
            "has_tickers": self.has_tickers,
            "event": self.event,
            "coordinate": self.coordinate,
            "signals": self.signals,
            "coverage": self.coverage,
            "entities": self.entities,
            "tickers": self.tickers,
            "ontology": self.ontology,
            "provenance": self.provenance,
            "timestamps": self.timestamps,
            "similar": self.similar,
            "oai_vector": self.oai_vector,
            "extra": self.extra
        }
        selected_fields = (
            self.present_fields & WORLD_EVENT_FIELDS
            if self.present_fields
            else WORLD_EVENT_FIELDS
        )
        data.update(
            {
                key: copy.deepcopy(x=value)
                for key, value in known_values.items()
                if key in selected_fields
            }
        )
        return data


class WorldEventPage:
    """Iterable World event page that retains all endpoint metadata."""

    def __init__(
        self: "WorldEventPage",
        events: List[WorldEvent],
        metadata: Optional[Dict[str, Any]] = None,
        bare: bool = False,
        events_field: str = "events"
    ) -> None:
        """
        Initialise a World event page.

        :param events: Parsed events in the page.
        :param metadata: Pagination and endpoint metadata.
        :param bare: Whether the source response was a bare event list.
        :param events_field: Envelope field containing the event list.
        :return: None.
        """
        self.events = events
        self.metadata = copy.deepcopy(x=metadata or {})
        self.bare = bare
        self.events_field = events_field
        for key, value in self.metadata.items():
            if key.isidentifier() and not hasattr(self, key):
                setattr(self, key, copy.deepcopy(x=value))
        self.total = self.metadata.get("total", len(events))
        self.count = self.metadata.get("count", len(events))
        self.next_cursor = self.metadata.get("next_cursor")
        self.facets = self.metadata.get("facets", {})

    def __len__(
        self: "WorldEventPage"
    ) -> int:
        """
        Return the number of events in the page.

        :return: Number of events.
        """
        return len(self.events)

    def __iter__(
        self: "WorldEventPage"
    ) -> Iterator[WorldEvent]:
        """
        Iterate over the events in the page.

        :return: Iterator over parsed events.
        """
        return iter(self.events)

    def __getitem__(
        self: "WorldEventPage",
        index: Union[int, slice]
    ) -> Union[WorldEvent, "WorldEventPage"]:
        """
        Return an event or sliced event page.

        :param index: Integer index or slice.
        :return: Selected event or page.
        """
        if isinstance(index, slice):
            return WorldEventPage(
                events=self.events[index],
                metadata=self.metadata,
                bare=self.bare,
                events_field=self.events_field
            )
        return self.events[index]

    @classmethod
    def from_dict(
        cls: "type[WorldEventPage]",
        data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> "WorldEventPage":
        """
        Parse an event page envelope or bare event list.

        :param data: World endpoint response.
        :return: Parsed event page.
        """
        if isinstance(data, list):
            return cls(
                events=[
                    WorldEvent.from_dict(data=item)
                    for item in data
                ],
                bare=True
            )
        if not isinstance(data, dict):
            raise ValueError(
                f"{MODULE_NAME}: WorldEventPage data must be a dictionary or list"
            )

        events_field = "events"
        if "events" in data:
            raw_events = data["events"]
        elif "response" in data:
            events_field = "response"
            raw_events = data["response"]
        else:
            raw_events = []
        if not isinstance(raw_events, list):
            raise ValueError(
                f"{MODULE_NAME}: WorldEventPage events must be a list"
            )

        metadata = {
            key: value
            for key, value in data.items()
            if key != events_field
        }
        return cls(
            events=[
                WorldEvent.from_dict(data=item)
                for item in raw_events
            ],
            metadata=metadata,
            events_field=events_field
        )

    def to_dict(
        self: "WorldEventPage"
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Convert the page to its lossless source representation.

        :return: World endpoint response payload.
        """
        events = [
            event.to_dict()
            for event in self.events
        ]
        if self.bare:
            return events

        data = copy.deepcopy(x=self.metadata)
        data[self.events_field] = events
        return data
