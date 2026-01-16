# tests/test_uda_inheritance.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from pydantic import Field, field_validator

from taskdantic import Priority, Status, Task, TWDatetime, TWDuration, UUIDList


class AgileTask(Task):
    """Task with Agile UDAs."""

    sprint: str | None = None
    points: int = 0
    estimate: TWDuration | None = None


class ValidatedTask(Task):
    """Task with validated UDAs."""

    points: int = Field(default=0, ge=0, le=100)
    sprint: str | None = None

    @field_validator("sprint")
    @classmethod
    def validate_sprint(cls, v: str | None) -> str | None:
        if v and not v.startswith("Sprint "):
            return f"Sprint {v}"
        return v


class ComplexTask(Task):
    """Task with complex UDA types."""

    reviewed: TWDatetime | None = None
    estimate: TWDuration | None = None
    blocked_by: UUIDList | None = None


def test_basic_uda_field_access():
    """Test basic UDA field access on Task subclass."""
    task = AgileTask(description="Test task", sprint="Sprint 23", points=8)

    assert task.description == "Test task"
    assert task.sprint == "Sprint 23"
    assert task.points == 8


def test_uda_field_type_coercion():
    """Test that UDA fields coerce types properly."""
    task = AgileTask(description="Test task", points="8")

    assert task.points == 8
    assert isinstance(task.points, int)


def test_uda_optional_fields():
    """Test optional UDA fields."""
    task = AgileTask(description="Test task")

    assert task.sprint is None
    assert task.points == 0


def test_uda_field_validation():
    """Test Pydantic validation on UDA fields."""
    with pytest.raises(Exception):  # ValidationError
        ValidatedTask(description="Test", points=150)


def test_uda_field_validator():
    """Test custom field validator on UDA."""
    task = ValidatedTask(description="Test", sprint="23")

    assert task.sprint == "Sprint 23"


def test_uda_datetime_field():
    """Test datetime UDA field."""
    reviewed = datetime(2024, 1, 20, 10, 0, 0, tzinfo=timezone.utc)
    task = ComplexTask(description="Test task", reviewed=reviewed)

    assert task.reviewed == reviewed


def test_uda_datetime_from_string():
    """Test datetime UDA parsing from Taskwarrior timestamp."""
    task = ComplexTask(description="Test task", reviewed="20240120T100000Z")

    expected = datetime(2024, 1, 20, 10, 0, 0, tzinfo=timezone.utc)
    assert task.reviewed == expected


def test_uda_timedelta_field():
    """Test timedelta UDA field."""
    task = AgileTask(description="Test task", estimate=timedelta(hours=2, minutes=30))

    assert task.estimate == timedelta(hours=2, minutes=30)


def test_uda_timedelta_from_string():
    """Test timedelta UDA parsing from ISO 8601 duration."""
    task = AgileTask(description="Test task", estimate="PT2H30M")

    assert task.estimate == timedelta(hours=2, minutes=30)


def test_uda_uuid_list_field():
    """Test UUID list UDA field."""
    uuid1 = UUID("12345678-1234-5678-1234-567812345678")
    uuid2 = UUID("87654321-4321-8765-4321-876543218765")

    task = ComplexTask(description="Test task", blocked_by=[uuid1, uuid2])

    assert task.blocked_by == [uuid1, uuid2]


def test_uda_uuid_list_from_string():
    """Test UUID list UDA parsing from comma-separated string."""
    task = ComplexTask(
        description="Test task",
        blocked_by="12345678-1234-5678-1234-567812345678,87654321-4321-8765-4321-876543218765",
    )

    uuid1 = UUID("12345678-1234-5678-1234-567812345678")
    uuid2 = UUID("87654321-4321-8765-4321-876543218765")

    assert task.blocked_by == [uuid1, uuid2]


def test_uda_export_dict():
    """Test exporting task with UDAs."""
    task = AgileTask(
        description="Test task",
        sprint="Sprint 23",
        points=8,
        estimate=timedelta(hours=4),
    )

    exported = task.export_dict()

    assert exported["description"] == "Test task"
    assert exported["sprint"] == "Sprint 23"
    assert exported["points"] == 8
    assert exported["estimate"] == "PT4H"


def test_uda_export_dict_exclude_none():
    """Test that None UDA fields are excluded from export."""
    task = AgileTask(description="Test task", points=5)

    exported = task.export_dict(exclude_none=True)

    assert "sprint" not in exported
    assert "estimate" not in exported
    assert exported["points"] == 5


def test_uda_datetime_export():
    """Test datetime UDA serialization."""
    reviewed = datetime(2024, 1, 20, 10, 0, 0, tzinfo=timezone.utc)
    task = ComplexTask(description="Test task", reviewed=reviewed)

    exported = task.export_dict()

    assert exported["reviewed"] == "20240120T100000Z"


def test_uda_timedelta_export():
    """Test timedelta UDA serialization."""
    task = AgileTask(description="Test task", estimate=timedelta(hours=2, minutes=30))

    exported = task.export_dict()

    assert exported["estimate"] == "PT2H30M"


def test_uda_uuid_list_export():
    """Test UUID list UDA serialization."""
    uuid1 = UUID("12345678-1234-5678-1234-567812345678")
    uuid2 = UUID("87654321-4321-8765-4321-876543218765")

    task = ComplexTask(description="Test task", blocked_by=[uuid1, uuid2])

    exported = task.export_dict()

    assert exported["blocked_by"] == "12345678-1234-5678-1234-567812345678,87654321-4321-8765-4321-876543218765"


def test_uda_from_taskwarrior():
    """Test importing task with UDAs from Taskwarrior."""
    data = {
        "uuid": "12345678-1234-5678-1234-567812345678",
        "description": "Test task",
        "status": "pending",
        "entry": "20240115T143022Z",
        "modified": "20240115T143022Z",
        "sprint": "Sprint 23",
        "points": 8,
        "estimate": "PT4H",
    }

    task = AgileTask.from_taskwarrior(data)

    assert task.description == "Test task"
    assert task.sprint == "Sprint 23"
    assert task.points == 8
    assert task.estimate == timedelta(hours=4)


def test_uda_from_taskwarrior_ignores_computed_fields():
    """Test that computed Taskwarrior fields are ignored."""
    data = {
        "uuid": "12345678-1234-5678-1234-567812345678",
        "description": "Test task",
        "status": "pending",
        "entry": "20240115T143022Z",
        "modified": "20240115T143022Z",
        "id": 42,
        "urgency": 5.2,
        "sprint": "Sprint 23",
    }

    task = AgileTask.from_taskwarrior(data)

    assert task.sprint == "Sprint 23"
    assert not hasattr(task, "id")
    assert not hasattr(task, "urgency")


def test_uda_roundtrip():
    """Test full export/import roundtrip with UDAs."""
    original = AgileTask(
        description="Test task",
        sprint="Sprint 23",
        points=8,
        estimate=timedelta(hours=4, minutes=30),
    )

    exported = original.export_dict()
    imported = AgileTask.from_taskwarrior(exported)

    assert imported.description == original.description
    assert imported.sprint == original.sprint
    assert imported.points == original.points
    assert imported.estimate == original.estimate


def test_uda_with_core_fields():
    """Test that UDAs work alongside core Task fields."""
    task = AgileTask(
        description="Test task",
        project="test_project",
        tags=["tag1", "tag2"],
        priority=Priority.HIGH,
        sprint="Sprint 23",
        points=8,
    )

    assert task.project == "test_project"
    assert task.tags == ["tag1", "tag2"]
    assert task.priority == Priority.HIGH
    assert task.sprint == "Sprint 23"
    assert task.points == 8


def test_multiple_task_types():
    """Test using different task subclasses for different purposes."""

    class BugTask(Task):
        severity: str = "medium"
        reported_by: str | None = None

    feature = AgileTask(description="Feature", sprint="Sprint 23", points=5)
    bug = BugTask(description="Bug", severity="high", reported_by="user@example.com")

    assert feature.sprint == "Sprint 23"
    assert bug.severity == "high"


def test_uda_inheritance_chain():
    """Test that UDA inheritance works across multiple levels."""

    class BaseTask(Task):
        base_field: str | None = None

    class ExtendedTask(BaseTask):
        extended_field: int = 0

    task = ExtendedTask(
        description="Test",
        base_field="base_value",
        extended_field=42,
    )

    assert task.base_field == "base_value"
    assert task.extended_field == 42

    exported = task.export_dict()
    assert exported["base_field"] == "base_value"
    assert exported["extended_field"] == 42


def test_unknown_uda_in_import():
    """Test that unknown UDAs from import are handled gracefully."""
    data = {
        "uuid": "12345678-1234-5678-1234-567812345678",
        "description": "Test task",
        "status": "pending",
        "entry": "20240115T143022Z",
        "modified": "20240115T143022Z",
        "sprint": "Sprint 23",
        "unknown_field": "some_value",
    }

    task = AgileTask.from_taskwarrior(data)

    assert task.sprint == "Sprint 23"
    # Unknown fields stored in __pydantic_extra__
    assert task.__pydantic_extra__["unknown_field"] == "some_value"


def test_uda_field_defaults():
    """Test that UDA field defaults work correctly."""

    class DefaultTask(Task):
        priority_score: float = 1.0
        complexity: int = Field(default=1)

    task = DefaultTask(description="Test")

    assert task.priority_score == 1.0
    assert task.complexity == 1


def test_uda_with_all_core_fields():
    """Test UDA task with all core fields populated."""
    task = AgileTask(
        description="Complex task",
        status=Status.PENDING,
        project="test_project",
        tags=["urgent", "work"],
        priority=Priority.HIGH,
        due=datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
        sprint="Sprint 23",
        points=8,
    )

    exported = task.export_dict()

    assert exported["description"] == "Complex task"
    assert exported["project"] == "test_project"
    assert exported["sprint"] == "Sprint 23"
    assert exported["points"] == 8


def test_empty_timedelta():
    """Test handling of zero-duration timedelta."""
    task = AgileTask(description="Test", estimate=timedelta(0))

    exported = task.export_dict()
    assert exported["estimate"] == "PT0S"

    imported = AgileTask.from_taskwarrior(exported)
    assert imported.estimate == timedelta(0)


def test_complex_timedelta():
    """Test handling of complex timedelta values."""
    task = AgileTask(description="Test", estimate=timedelta(hours=10, minutes=45, seconds=30))

    exported = task.export_dict()
    assert exported["estimate"] == "PT10H45M30S"

    imported = AgileTask.from_taskwarrior(exported)
    assert imported.estimate == timedelta(hours=10, minutes=45, seconds=30)
