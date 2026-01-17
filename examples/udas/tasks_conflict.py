from __future__ import annotations

from pydantic import Field
from taskdantic import Task


class ConflictingTask(Task):
    # Same UDA name as AgileTask.points, but different type -> should raise during merge
    conflict_points: str | None = Field(
        default=None,
        json_schema_extra={"taskwarrior": {"label": "Points (BAD)"}},
    )
