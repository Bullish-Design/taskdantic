# src/taskdantic/models.py

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from taskdantic.serializers import (
    duration_serializer,
    duration_validator,
    taskwarrior_datetime_serializer,
    taskwarrior_datetime_validator,
)
from taskdantic.types import Priority, TaskStatus


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

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        """Validate that description is not empty."""
        if not value or not value.strip():
            raise ValueError("Description cannot be empty")
        return value

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
        when_used="json",
    )
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to Taskwarrior format."""
        return taskwarrior_datetime_serializer(value)

    @field_validator("recur", mode="before")
    @classmethod
    def validate_recur(cls, value: Any) -> Optional[timedelta]:
        """Validate and parse recur field."""
        return duration_validator(value)

    @field_serializer("recur", when_used="json")
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

    @field_serializer("depends", when_used="json")
    def serialize_depends(self, value: list[UUID]) -> Optional[str]:
        """Serialize depends as comma-separated UUIDs."""
        if not value:
            return None
        return ",".join(str(uuid) for uuid in value)

    @field_serializer("uuid", "parent", when_used="json")
    def serialize_uuid(self, value: Optional[UUID]) -> Optional[str]:
        """Serialize UUID fields to string."""
        return str(value) if value else None

    @field_serializer("tags", when_used="json")
    def serialize_tags(self, value: list[str]) -> Optional[list[str]]:
        """Serialize tags, return None if empty."""
        return value if value else None

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )


class UDADefinition(BaseModel):
    """User-Defined Attribute definition."""

    type: str
    label: Optional[str] = None
    values: Optional[list[str]] = None

    model_config = ConfigDict(extra="allow")


class TaskConfig(BaseModel):
    """Taskwarrior configuration."""

    data_location: Optional[str] = Field(None, alias="data.location")
    udas: dict[str, UDADefinition] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> TaskConfig:
        """Load TaskConfig from YAML file.

        Args:
            yaml_path: Path to YAML config file

        Returns:
            TaskConfig instance
        """
        path = Path(yaml_path).expanduser()
        if not path.exists():
            return cls()

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Extract UDAs
        udas_dict = data.pop("udas", {})
        udas = {}
        for name, uda_data in udas_dict.items():
            if isinstance(uda_data, dict):
                udas[name] = UDADefinition(**uda_data)

        # Extract data.location
        data_location = None
        if "data" in data and isinstance(data["data"], dict):
            data_location = data["data"].get("location")

        return cls(
            data_location=data_location,
            udas=udas,
            config=data,
        )

    def write_taskrc(self, output_path: str | Path) -> None:
        """Write configuration to .taskrc format.

        Args:
            output_path: Path where .taskrc should be written
        """
        from taskdantic.config_writer import TaskRcWriter

        # Reconstruct full config dict
        full_config = self.config.copy()
        if self.udas:
            full_config["udas"] = {
                name: uda.model_dump(exclude_none=True) for name, uda in self.udas.items()
            }

        # Write to temporary YAML then convert
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(full_config, f)
            temp_yaml = f.name

        try:
            writer = TaskRcWriter(temp_yaml)
            writer.write_taskrc(output_path)
        finally:
            Path(temp_yaml).unlink(missing_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by key using dot notation.

        Args:
            key: Config key with dot notation
            default: Default value if key not found

        Returns:
            Config value or default
        """
        parts = key.split(".")
        current = self.config

        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]

        return current

    def get_udas(self) -> dict[str, dict[str, Any]]:
        """Get all UDA definitions as a dict.

        Returns:
            Dictionary of UDA definitions
        """
        result: dict[str, dict[str, Any]] = {}
        for name, uda_def in self.udas.items():
            result[name] = {
                "type": uda_def.type,
                "label": uda_def.label,
            }
            if uda_def.values:
                result[name]["values"] = ",".join(uda_def.values)
        return result
