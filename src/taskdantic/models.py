# src/taskdantic/models.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_serializer,
    field_validator,
    model_validator,
    ValidationInfo,
)

from taskdantic.enums import Priority, Status
from taskdantic.task_types import TWDatetime, UUIDList


def _utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


class Annotation(BaseModel):
    """Task annotation with timestamp."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    entry: TWDatetime = Field(default_factory=_utc_now)
    description: str = Field(min_length=1)


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

    CORE_FIELDS: ClassVar[set[str]] = {
        "uuid",
        "description",
        "status",
        "entry",
        "modified",
        "due",
        "scheduled",
        "start",
        "end",
        "wait",
        "until",
        "project",
        "tags",
        "priority",
        "annotations",
        "depends",
    }

    COMPUTED_FIELDS: ClassVar[set[str]] = {
        "id",
        "urgency",
        "mask",
        "imask",
        "parent",
        "recur",
    }

    uuid: UUID = Field(default_factory=uuid4)
    description: str = Field(min_length=1)
    status: Status = Status.PENDING
    entry: TWDatetime = Field(default_factory=_utc_now)
    modified: TWDatetime = Field(default_factory=_utc_now)
    due: TWDatetime | None = None
    scheduled: TWDatetime | None = None
    start: TWDatetime | None = None
    end: TWDatetime | None = None
    wait: TWDatetime | None = None
    until: TWDatetime | None = None
    project: str | None = None
    tags: list[str] = Field(default_factory=list)
    priority: Priority | None = None
    annotations: list[Annotation] = Field(default_factory=list)
    depends: UUIDList = Field(default_factory=list)

    @field_serializer("uuid")
    def serialize_uuid(self, value: UUID) -> str:
        """Serialize UUID to string for Taskwarrior."""
        return str(value)

    @model_validator(mode="after")
    def validate_business_rules(self) -> Task:
        """Validate business rules after all fields are set."""
        # Auto-set end timestamp for completed tasks if missing
        if self.status == Status.COMPLETED and self.end is None:
            self.end = self.modified

        # Clear end timestamp for non-completed tasks
        # (this handles state transitions gracefully)
        if self.status != Status.COMPLETED and self.end is not None:
            # Don't raise error, just warn via return
            # This allows importing of malformed data
            pass

        return self

    # Computed properties

    @computed_field
    @property
    def is_active(self) -> bool:
        """Return True if task is started but not completed."""
        return self.status == Status.PENDING and self.start is not None

    @computed_field
    @property
    def is_blocked(self) -> bool:
        """Return True if task has dependencies."""
        return len(self.depends) > 0

    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Return True if task has a due date in the past."""
        if self.due is None:
            return False
        return self.due < _utc_now() and self.status == Status.PENDING

    @computed_field
    @property
    def is_waiting(self) -> bool:
        """Return True if task is waiting."""
        return self.status == Status.WAITING

    @computed_field
    @property
    def days_until_due(self) -> float | None:
        """Return number of days until due date, or None if no due date."""
        if self.due is None:
            return None
        delta = self.due - _utc_now()
        return delta.total_seconds() / 86400

    # Business logic methods

    def complete(self) -> None:
        """
        Mark task as completed.

        Raises:
            ValueError: If task is deleted or already completed
        """
        if self.status == Status.DELETED:
            raise ValueError("Cannot complete deleted task")
        if self.status == Status.COMPLETED:
            raise ValueError("Task is already completed")

        self.status = Status.COMPLETED
        self.end = _utc_now()
        self.modified = _utc_now()

    def start_task(self) -> None:
        """
        Start the task by setting start timestamp.

        Raises:
            ValueError: If task is not pending
        """
        if self.status != Status.PENDING:
            raise ValueError(f"Cannot start task with status: {self.status.value}")
        if self.start is not None:
            raise ValueError("Task is already started")

        self.start = _utc_now()
        self.modified = _utc_now()

    def stop_task(self) -> None:
        """
        Stop the task by clearing start timestamp.

        Raises:
            ValueError: If task is not started
        """
        if self.start is None:
            raise ValueError("Task is not started")

        self.start = None
        self.modified = _utc_now()

    def delete(self) -> None:
        """
        Mark task as deleted.

        Raises:
            ValueError: If task is already deleted
        """
        if self.status == Status.DELETED:
            raise ValueError("Task is already deleted")

        self.status = Status.DELETED
        self.end = _utc_now()
        self.modified = _utc_now()

    def add_dependency(self, task: Task | UUID) -> None:
        """
        Add a task dependency.

        Args:
            task: Task instance or UUID to depend on
        """
        uuid_to_add = task.uuid if isinstance(task, Task) else task
        if uuid_to_add == self.uuid:
            raise ValueError("Task cannot depend on itself")
        if uuid_to_add not in self.depends:
            self.depends.append(uuid_to_add)
            self.modified = _utc_now()

    def remove_dependency(self, task: Task | UUID) -> None:
        """
        Remove a task dependency.

        Args:
            task: Task instance or UUID to remove from dependencies
        """
        uuid_to_remove = task.uuid if isinstance(task, Task) else task
        if uuid_to_remove in self.depends:
            self.depends.remove(uuid_to_remove)
            self.modified = _utc_now()

    def add_annotation(self, description: str, entry: datetime | None = None) -> None:
        """
        Add an annotation to the task.

        Args:
            description: Annotation text
            entry: Annotation timestamp (defaults to now)
        """
        annotation = Annotation(
            entry=entry if entry is not None else _utc_now(),
            description=description,
        )
        self.annotations.append(annotation)
        self.modified = _utc_now()

    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the task.

        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.modified = _utc_now()

    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the task.

        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.modified = _utc_now()

    def has_tag(self, tag: str) -> bool:
        """
        Check if task has a specific tag.

        Args:
            tag: Tag to check

        Returns:
            True if task has the tag
        """
        return tag in self.tags

    # UDA methods

    @classmethod
    def core_field_names(cls) -> set[str]:
        """
        Return the stable set of Task core field names (excluding subclass UDAs).
        """
        return set(cls.CORE_FIELDS)

    @classmethod
    def is_core_field(cls, name: str) -> bool:
        """
        Return True if `name` is part of the Task core schema or a computed field.
        """
        return (
            name in cls.core_field_names()
            or name in cls.model_computed_fields
            or name in cls.COMPUTED_FIELDS
        )

    def get_udas(self) -> dict[str, Any]:
        """
        Return all User Defined Attributes (UDAs).

        UDAs include:
          - subclass-declared fields, and
          - extra fields allowed by `extra="allow"` on the base model config.
        """
        core = self.__class__.core_field_names()
        computed = set(self.__class__.model_computed_fields.keys()).union(self.__class__.COMPUTED_FIELDS)

        # Dump without computed fields so they don't get misclassified as UDAs.
        all_data = self.model_dump(exclude=computed)

        return {
            k: v
            for k, v in all_data.items()
            if k not in core and k not in self.__class__.COMPUTED_FIELDS and not k.startswith("_")
        }

    def model_dump_udas(self, exclude_none: bool = True) -> dict[str, Any]:
        """
        Dump only UDAs, using the same serialization rules as `to_taskwarrior()`.

        This returns Taskwarrior-ready values (e.g., TWDatetime serialized to strings,
        UUIDList serialized to comma-separated strings, etc.), consistent with
        `to_taskwarrior()`. :contentReference[oaicite:2]{index=2}
        """
        data = self.to_taskwarrior(exclude_none=exclude_none)
        core = self.__class__.core_field_names()

        return {
            k: v
            for k, v in data.items()
            if k not in core and k not in self.__class__.COMPUTED_FIELDS and not k.startswith("_")
        }

    @property
    def uda_names(self) -> list[str]:
        """Return names of all UDAs."""
        return list(self.get_udas().keys())

    # Serialization methods

    def to_taskwarrior(self, exclude_none: bool = True) -> dict[str, Any]:
        """
        Export task to Taskwarrior JSON format.

        Args:
            exclude_none: Whether to exclude None values from output

        Returns:
            Dictionary in Taskwarrior JSON format
        """
        data = self.model_dump(
            mode="json",
            exclude_none=exclude_none,
            by_alias=False,
            exclude=set(self.__class__.model_computed_fields.keys()),
        )

        # Additional cleanup: remove None values that came from serialization
        # (e.g., empty UUIDList -> None) when exclude_none is True
        if exclude_none:
            data = {k: v for k, v in data.items() if v is not None}

        return data

    def export_dict(self, exclude_none: bool = True) -> dict[str, Any]:
        """
        Export task to dictionary (backward compatibility alias for to_taskwarrior).

        Args:
            exclude_none: Whether to exclude None values from output

        Returns:
            Dictionary in Taskwarrior JSON format
        """
        return self.to_taskwarrior(exclude_none=exclude_none)

    def to_json(self, **kwargs: Any) -> str:
        """
        Serialize task to JSON string.

        Args:
            **kwargs: Additional arguments passed to model_dump_json

        Returns:
            JSON string representation
        """
        return self.model_dump_json(exclude=set(self.model_computed_fields.keys()), **kwargs)

    @classmethod
    def from_json(cls, json_str: str) -> Task:
        """
        Deserialize task from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            Validated Task instance

        Raises:
            ValidationError: If JSON is invalid or validation fails
        """
        return cls.model_validate_json(json_str)

    @classmethod
    def from_taskwarrior(cls, data: dict[str, Any]) -> Task:
        """
        Parse task from Taskwarrior export JSON.

        Automatically filters out computed Taskwarrior fields like 'id',
        'urgency', 'mask', etc., which should not be persisted.

        Args:
            data: Raw task dictionary from Taskwarrior export

        Returns:
            Validated Task instance

        Raises:
            ValidationError: If required fields are missing or invalid

        Example:
            >>> task_dict = {"description": "Test", "status": "pending", ...}
            >>> task = Task.from_taskwarrior(task_dict)
        """
        clean_data = {k: v for k, v in data.items() if k not in cls.COMPUTED_FIELDS}
        return cls.model_validate(clean_data)
