"""Models for the nested Rich Search response."""

import os
import copy
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set, Tuple

MODULE_NAME = os.path.basename(p=__file__)
RICH_RESULT_FIELDS: Tuple[str, ...] = (
    "page",
    "snippet",
    "tokens",
    "semantics",
    "profile",
    "targeting",
    "history",
    "signals",
    "vectors"
)


@dataclass
class RichResult:
    """One losslessly represented result from Rich Search."""

    page: Optional[Dict[str, Any]] = field(default_factory=dict)
    snippet: Optional[Dict[str, Any]] = field(default_factory=dict)
    tokens: Optional[Dict[str, Any]] = field(default_factory=dict)
    semantics: Optional[Dict[str, Any]] = field(default_factory=dict)
    profile: Optional[Dict[str, Any]] = None
    targeting: Optional[Dict[str, Any]] = None
    history: Optional[Dict[str, Any]] = None
    signals: Optional[Dict[str, Any]] = None
    vectors: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = field(
        default_factory=dict,
        repr=False
    )
    present_fields: Set[str] = field(
        default_factory=set,
        repr=False,
        compare=False
    )

    @property
    def similarity(
        self: "RichResult"
    ) -> Optional[float]:
        """
        Return the semantic similarity score.

        :return: Similarity score when supplied by the API.
        """
        if self.semantics is None:
            return None
        return self.semantics.get("similarity")

    @classmethod
    def from_dict(
        cls: "type[RichResult]",
        data: Dict[str, Any]
    ) -> "RichResult":
        """
        Create a rich result without discarding unknown response fields.

        :param data: Rich Search result payload.
        :return: Parsed rich result.
        """
        if not isinstance(data, dict):
            raise ValueError(
                f"{MODULE_NAME}: RichResult data must be a dictionary"
            )

        return cls(
            page=(
                copy.deepcopy(x=data["page"])
                if "page" in data
                else {}
            ),
            snippet=(
                copy.deepcopy(x=data["snippet"])
                if "snippet" in data
                else {}
            ),
            tokens=(
                copy.deepcopy(x=data["tokens"])
                if "tokens" in data
                else {}
            ),
            semantics=(
                copy.deepcopy(x=data["semantics"])
                if "semantics" in data
                else {}
            ),
            profile=copy.deepcopy(x=data.get("profile")),
            targeting=copy.deepcopy(x=data.get("targeting")),
            history=copy.deepcopy(x=data.get("history")),
            signals=copy.deepcopy(x=data.get("signals")),
            vectors=copy.deepcopy(x=data.get("vectors")),
            extra={
                key: copy.deepcopy(x=value)
                for key, value in data.items()
                if key not in RICH_RESULT_FIELDS
            },
            present_fields=set(data)
        )

    def to_dict(
        self: "RichResult"
    ) -> Dict[str, Any]:
        """
        Convert the rich result to its lossless dictionary representation.

        :return: Rich Search result payload.
        """
        data = copy.deepcopy(x=self.extra)
        if self.present_fields:
            selected_fields = self.present_fields
        else:
            selected_fields = {
                "page",
                "snippet",
                "tokens",
                "semantics",
                *(
                    name
                    for name in RICH_RESULT_FIELDS[4:]
                    if getattr(self, name) is not None
                )
            }

        for name in RICH_RESULT_FIELDS:
            if name in selected_fields:
                data[name] = copy.deepcopy(x=getattr(self, name))

        return data
