from __future__ import annotations

from enum import Enum
from typing import Literal
from datetime import timedelta

from pydantic import Field

from taskdantic import Task, TWDuration, TWDatetime


class Sprint(str, Enum):
    S23 = "S23"
    S24 = "S24"


class AgileTask(Task):
    sprint: Sprint | None = Field(
        default=None,
        json_schema_extra={"taskwarrior": {"label": "Sprint"}},
    )

    points: int = Field(
        default=0,
        json_schema_extra={"taskwarrior": {"label": "Points"}},
    )

    estimate: TWDuration | None = Field(
        default=None,
        json_schema_extra={"taskwarrior": {"label": "Estimate"}},
    )

    reviewed: TWDatetime | None = Field(
        default=None,
        json_schema_extra={"taskwarrior": {"label": "Reviewed"}},
    )

    stage: Literal["todo", "doing", "done"] | None = Field(
        default=None,
        json_schema_extra={
            "taskwarrior": {
                "label": "Stage",
                "values": ["todo", "doing", "done"],
                "urgency": {"doing": 2.0, "done": -1.0},
            }
        },
    )
