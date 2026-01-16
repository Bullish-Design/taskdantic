# src/taskdantic/models.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, ClassVar, get_args, get_origin
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

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
    """
    Pydantic model for Taskwarrior task format.

    Supports User Defined Attributes (UDAs) through inheritance:

    Example:
        class AgileTask(Task):
            sprint: str | None = None
            points: int = 0
            estimate: timedelta | None = None

        task = AgileTask(description="Deploy app", sprint="Sprint 23", points=8)
    """

    model_config = ConfigDict(extra="allow", validate_assignment=True)

    # Core taskwarrior fields
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

    @classmethod
    def _get_uda_fields(cls) -> set[str]:
        """Get field names that are UDAs (not core Taskwarrior fields)."""
        all_fields = set(cls.model_fields.keys())
        return all_fields - cls._CORE_FIELDS

    @classmethod
    def _parse_uda_value(cls, field_name: str, value: Any) -> Any:
        """Parse a UDA value based on its field type."""
        if field_name not in cls.model_fields:
            return value

        field_info = cls.model_fields[field_name]
        field_type = field_info.annotation

        # Handle Optional types (X | None)
        origin = get_origin(field_type)
        if origin is type(None) | type:
            args = get_args(field_type)
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                field_type = non_none_types[0]

        # Parse datetime (Taskwarrior timestamp format)
        if field_type is datetime:
            if isinstance(value, str):
                return taskwarrior_to_datetime(value)
            return value

        # Parse timedelta (ISO 8601 duration format)
        if field_type is timedelta:
            return cls._parse_duration(value)

        # Parse UUID list (comma-separated string)
        if get_origin(field_type) is list:
            args = get_args(field_type)
            if args and args[0] is UUID:
                return cls._parse_uuid_list(value)

        return value

    @classmethod
    def _serialize_uda_value(cls, field_name: str, value: Any) -> Any:
        """Serialize a UDA value based on its field type."""
        if value is None:
            return None

        if field_name not in cls.model_fields:
            return value

        field_info = cls.model_fields[field_name]
        field_type = field_info.annotation

        # Handle Optional types
        origin = get_origin(field_type)
        if origin is type(None) | type:
            args = get_args(field_type)
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                field_type = non_none_types[0]

        # Serialize datetime to Taskwarrior format
        if field_type is datetime:
            return datetime_to_taskwarrior(value)

        # Serialize timedelta to ISO 8601 duration
        if field_type is timedelta:
            return cls._serialize_duration(value)

        # Serialize UUID list to comma-separated string
        if get_origin(field_type) is list:
            args = get_args(field_type)
            if args and args[0] is UUID:
                return cls._serialize_uuid_list(value)

        return value

    @staticmethod
    def _parse_duration(v: str | timedelta) -> timedelta:
        """Parse ISO 8601 duration string."""
        if isinstance(v, timedelta):
            return v
        if isinstance(v, str) and v.startswith("PT"):
            hours = 0
            minutes = 0
            seconds = 0
            v = v[2:]
            if "H" in v:
                hours_str, v = v.split("H", 1)
                hours = int(hours_str)
            if "M" in v:
                minutes_str, v = v.split("M", 1)
                minutes = int(minutes_str)
            if "S" in v:
                seconds = int(v.replace("S", ""))
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        return timedelta(seconds=int(v))

    @staticmethod
    def _serialize_duration(v: timedelta) -> str:
        """Serialize timedelta to ISO 8601 duration string."""
        total_seconds = int(v.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        parts = []
        if hours:
            parts.append(f"{hours}H")
        if minutes:
            parts.append(f"{minutes}M")
        if seconds:
            parts.append(f"{seconds}S")
        return "PT" + "".join(parts) if parts else "PT0S"

    @staticmethod
    def _parse_uuid_list(v: str | list) -> list[UUID]:
        """Parse comma-separated UUID string or list."""
        if isinstance(v, list):
            return [UUID(u) if isinstance(u, str) else u for u in v]
        if isinstance(v, str):
            return [UUID(u.strip()) for u in v.split(",") if u.strip()]
        return []

    @staticmethod
    def _serialize_uuid_list(v: list[UUID]) -> str | None:
        """Serialize UUID list to comma-separated string."""
        return ",".join(str(u) for u in v) if v else None

    def export_dict(self, exclude_none: bool = True) -> dict[str, Any]:
        """Export task as dict suitable for Taskwarrior import."""
        data = self.model_dump(
            mode="json",
            exclude_none=exclude_none,
            by_alias=False,
        )

        # Serialize UDA fields with custom logic
        uda_fields = self._get_uda_fields()
        for field_name in uda_fields:
            if field_name in data:
                value = getattr(self, field_name)
                serialized = self._serialize_uda_value(field_name, value)
                if serialized is not None or not exclude_none:
                    data[field_name] = serialized
                elif serialized is None and exclude_none:
                    data.pop(field_name, None)

        # Remove empty lists that were serialized to None
        if exclude_none:
            data = {k: v for k, v in data.items() if v is not None}

        return data

    @classmethod
    def from_taskwarrior(cls, data: dict[str, Any]) -> Task:
        """Parse task from Taskwarrior export JSON."""
        # Separate core fields, UDAs, and computed fields
        clean_data = {}
        uda_data = {}

        for key, value in data.items():
            if key in ("id", "urgency", "mask", "imask", "parent", "recur"):
                # Skip computed/internal Taskwarrior fields
                continue
            elif key in cls._CORE_FIELDS:
                clean_data[key] = value
            else:
                # This is a UDA - parse it if we have a field definition
                uda_data[key] = cls._parse_uda_value(key, value)

        # Merge core and UDA data
        clean_data.update(uda_data)

        return cls.model_validate(clean_data)
