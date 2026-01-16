# src/taskdantic/models.py
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_serializer, field_validator

from taskdantic.enums import Priority, Status
from taskdantic.utils import datetime_to_taskwarrior, taskwarrior_to_datetime


class Annotation(BaseModel):
    """Task annotation with timestamp and description."""

    entry: datetime
    description: str

    @field_validator("entry", mode="before")
    @classmethod
    def parse_entry(cls, value: str | datetime) -> datetime:
        if isinstance(value, str):
            return taskwarrior_to_datetime(value)
        return value

    @field_serializer("entry")
    def serialize_entry(self, value: datetime) -> str:
        return datetime_to_taskwarrior(value)


class Task(BaseModel):
    """Pydantic model for Taskwarrior task format."""

    uuid: UUID = Field(default_factory=uuid4)
    description: str
    status: Status = Status.PENDING

    entry: datetime = Field(default_factory=lambda: datetime.now())
    modified: datetime = Field(default_factory=lambda: datetime.now())

    project: str | None = None
    tags: list[str] = Field(default_factory=list)
    priority: Priority | None = None

    due: datetime | None = None
    scheduled: datetime | None = None
    start: datetime | None = None
    end: datetime | None = None
    wait: datetime | None = None
    until: datetime | None = None

    annotations: list[Annotation] = Field(default_factory=list)
    depends: list[UUID] = Field(default_factory=list)

    @field_validator("entry", "modified", "due", "scheduled", "start", "end", "wait", "until", mode="before")
    @classmethod
    def parse_datetime(cls, value: str | datetime | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, str):
            return taskwarrior_to_datetime(value)
        return value

    @field_serializer("entry", "modified", "due", "scheduled", "start", "end", "wait", "until")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return datetime_to_taskwarrior(value)

    @field_serializer("uuid")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    @field_validator("depends", mode="before")
    @classmethod
    def parse_depends(cls, value: list[str] | list[UUID] | str | None) -> list[UUID]:
        if value is None:
            return []
        if isinstance(value, str):
            return [UUID(value)]
        return [UUID(dep) if isinstance(dep, str) else dep for dep in value]

    @field_serializer("depends")
    def serialize_depends(self, value: list[UUID]) -> str | None:
        if not value:
            return None
        return ",".join(str(uuid) for uuid in value)

    def export_dict(self, exclude_none: bool = True) -> dict[str, Any]:
        """Export task as dict suitable for Taskwarrior import."""
        data = self.model_dump(
            mode="json",
            exclude_none=exclude_none,
            by_alias=False,
        )
        # Remove empty lists that were serialized to None
        if exclude_none:
            data = {k: v for k, v in data.items() if v is not None}
        return data

    @classmethod
    def from_taskwarrior(cls, data: dict[str, Any]) -> Task:
        """Parse task from Taskwarrior export JSON."""
        clean_data = {k: v for k, v in data.items() if k not in ("id", "urgency")}
        return cls.model_validate(clean_data)
