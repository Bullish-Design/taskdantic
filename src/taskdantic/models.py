# src/taskdantic/models.py

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from taskdantic.types import Priority, TaskStatus
from taskdantic.utils import (
    duration_serializer,
    duration_validator,
    taskwarrior_datetime_serializer,
    taskwarrior_datetime_validator,
)


class Annotation(BaseModel):
    """Task annotation with timestamp and description."""

    entry: datetime
    description: str

    @field_validator("entry", mode="before")
    @classmethod
    def validate_entry(cls, value: Any) -> datetime:
        """Validate and parse entry datetime."""
        result = taskwarrior_datetime_validator(value)
        if result is None:
            raise ValueError("Annotation entry cannot be None")
        return result

    @field_serializer("entry")
    def serialize_entry(self, value: datetime) -> str:
        """Serialize entry to Taskwarrior format."""
        result = taskwarrior_datetime_serializer(value)
        if result is None:
            raise ValueError("Cannot serialize None entry")
        return result

    model_config = ConfigDict(populate_by_name=True)


class Task(BaseModel):
    """Pydantic model for a Taskwarrior task."""

    # Core fields
    uuid: Optional[UUID] = None
    id: Optional[int] = Field(None, exclude=True)
    description: str
    status: TaskStatus = TaskStatus.PENDING

    # Optional fields
    project: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    priority: Optional[Priority] = None

    # Dates
    entry: Optional[datetime] = None
    modified: Optional[datetime] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    due: Optional[datetime] = None
    until: Optional[datetime] = None
    wait: Optional[datetime] = None
    scheduled: Optional[datetime] = None

    # Dependencies
    depends: list[UUID] = Field(default_factory=list)
    parent: Optional[UUID] = None

    # Recurrence
    recur: Optional[timedelta] = None
    mask: Optional[str] = None
    imask: Optional[int] = None

    # Annotations
    annotations: list[Annotation] = Field(default_factory=list)

    # Computed (read-only)
    urgency: Optional[float] = Field(None, exclude=True)

    @field_validator(
        "entry",
        "modified",
        "start",
        "end",
        "due",
        "until",
        "wait",
        "scheduled",
        mode="before",
    )
    @classmethod
    def validate_datetime(cls, value: Any) -> Optional[datetime]:
        """Validate and parse datetime fields."""
        return taskwarrior_datetime_validator(value)

    @field_serializer(
        "entry",
        "modified",
        "start",
        "end",
        "due",
        "until",
        "wait",
        "scheduled",
    )
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to Taskwarrior format."""
        return taskwarrior_datetime_serializer(value)

    @field_validator("recur", mode="before")
    @classmethod
    def validate_recur(cls, value: Any) -> Optional[timedelta]:
        """Validate and parse recur field."""
        return duration_validator(value)

    @field_serializer("recur")
    def serialize_recur(self, value: Optional[timedelta]) -> Optional[str]:
        """Serialize recur to Taskwarrior duration format."""
        return duration_serializer(value)

    @field_validator("depends", mode="before")
    @classmethod
    def validate_depends(cls, value: Any) -> list[UUID]:
        """Validate depends field - handle comma-separated UUIDs."""
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [UUID(str(v)) if not isinstance(v, UUID) else v for v in value]
        if isinstance(value, str):
            if "," in value:
                return [UUID(dep.strip()) for dep in value.split(",") if dep.strip()]
            return [UUID(value)]
        raise TypeError(f"Expected list or str for depends, got {type(value)}")

    @field_serializer("depends")
    def serialize_depends(self, value: list[UUID]) -> Optional[str]:
        """Serialize depends as comma-separated UUIDs."""
        if not value:
            return None
        return ",".join(str(uuid) for uuid in value)

    @field_serializer("uuid", "parent")
    def serialize_uuid(self, value: Optional[UUID]) -> Optional[str]:
        """Serialize UUID fields to string."""
        return str(value) if value else None

    @field_serializer("tags")
    def serialize_tags(self, value: list[str]) -> Optional[list[str]]:
        """Serialize tags, return None if empty."""
        return value if value else None

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )


class UDADefinition(BaseModel):
    """User-Defined Attribute definition from taskrc."""

    type: str
    label: Optional[str] = None
    values: Optional[list[str]] = None

    model_config = ConfigDict(extra="allow")


class TaskConfig(BaseModel):
    """Taskwarrior configuration from taskrc file."""

    data_location: Optional[str] = Field(None, alias="data.location")
    udas: dict[str, UDADefinition] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
