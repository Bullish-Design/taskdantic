from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from taskdantic.enums import Priority, Status

# from taskdantic.utils import datetime_to_taskwarrior, taskwarrior_to_datetime
from taskdantic.types import TWDatetime, UUIDList


class Annotation(BaseModel):
    entry: TWDatetime
    description: str


class Task(BaseModel):
    """
    Pydantic model for Taskwarrior task format.

    Supports User Defined Attributes (UDAs) through inheritance.
    Use TWDatetime, TWDuration, and UUIDList types for Taskwarrior-compatible fields.

    Example:
        from taskdantic import Task, TWDatetime, TWDuration

        class AgileTask(Task):
            sprint: str | None = None
            points: int = 0
            estimate: TWDuration | None = None
            reviewed: TWDatetime | None = None

        task = AgileTask(
            description="Deploy app",
            sprint="Sprint 23",
            points=8,
            estimate="PT6H"
        )
    """

    model_config = ConfigDict(extra="allow", validate_assignment=True)

    # Core taskwarrior fields
    uuid: UUID = Field(default_factory=uuid4)
    description: str
    status: Status = Status.PENDING

    # use tz-aware UTC defaults
    entry: TWDatetime = Field(default_factory=lambda: TWDatetime.now(timezone.utc))
    modified: TWDatetime = Field(default_factory=lambda: TWDatetime.now(timezone.utc))

    project: str | None = None
    tags: list[str] = Field(default_factory=list)
    priority: Priority | None = None

    # timestamps
    due: TWDatetime | None = None
    scheduled: TWDatetime | None = None
    start: TWDatetime | None = None
    end: TWDatetime | None = None
    wait: TWDatetime | None = None
    until: TWDatetime | None = None

    annotations: list[Annotation] = Field(default_factory=list)

    # depends uses the same adapter as UDAs
    depends: UUIDList = Field(default_factory=UUIDList)

    # Core taskwarrior field names (including common computed fields to ignore)
    _CORE_FIELDS: ClassVar[set[str]] = {
        "uuid",
        "description",
        "status",
        "entry",
        "modified",
        "project",
        "tags",
        "priority",
        "due",
        "scheduled",
        "start",
        "end",
        "wait",
        "until",
        "annotations",
        "depends",
        "id",
        "urgency",
        "mask",
        "imask",
        "parent",
        "recur",
    }

    _COMPUTED_FIELDS_TO_IGNORE: ClassVar[set[str]] = {
        "id",
        "urgency",
        "mask",
        "imask",
        "parent",
        "recur",
    }

    @field_serializer("uuid")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    def export_dict(self, exclude_none: bool = True) -> dict[str, Any]:
        data = self.model_dump(mode="json", exclude_none=exclude_none, by_alias=False)
        if exclude_none:
            data = {k: v for k, v in data.items() if v is not None}
        return data

    @classmethod
    def from_taskwarrior(cls, data: dict[str, Any]) -> Task:
        """Parse task from Taskwarrior export JSON."""
        # Filter out computed/internal Taskwarrior fields
        # clean_data = {k: v for k, v in data.items() if k not in ("id", "urgency", "mask", "imask", "parent", "recur")}
        clean_data = {k: v for k, v in data.items() if k not in cls._COMPUTED_FIELDS_TO_IGNORE}
        return cls.model_validate(clean_data)
