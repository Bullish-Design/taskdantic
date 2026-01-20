from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field

from taskdantic import Task, TWDuration, TWDatetime, uda


class Sprint(str, Enum):
    S23 = "S23"
    S24 = "S24"


class AgileTask(Task):
    sprint: Sprint | None = Field(
        default=None,
        json_schema_extra=uda(label="Sprint"),
    )

    points: int = Field(
        default=0,
        json_schema_extra=uda(label="Points"),
    )

    estimate: TWDuration | None = Field(
        default=None,
        json_schema_extra=uda(label="Estimate"),
    )

    reviewed: TWDatetime | None = Field(
        default=None,
        json_schema_extra=uda(label="Reviewed"),
    )

    stage: Literal["todo", "doing", "done"] | None = Field(
        default=None,
        json_schema_extra=uda(
            label="Stage",
            values=["todo", "doing", "done"],
            urgency={"doing": 2.0, "done": -1.0},
        ),
    )
