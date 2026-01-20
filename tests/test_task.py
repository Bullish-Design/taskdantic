# tests/test_task.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

from taskdantic import Priority, Status, Task
from taskdantic.models import Annotation


def test_task_minimal_creation():
    """Test creating task with only required fields."""
    task = Task(description="Test task")

    assert task.description == "Test task"
    assert task.status == Status.PENDING
    assert isinstance(task.uuid, UUID)
    assert isinstance(task.entry, datetime)
    assert isinstance(task.modified, datetime)


def test_task_with_all_common_fields():
    """Test creating task with common fields."""
    task = Task(
        description="Test task",
        status=Status.PENDING,
        project="test_project",
        tags=["tag1", "tag2"],
        priority=Priority.HIGH,
    )

    assert task.project == "test_project"
    assert task.tags == ["tag1", "tag2"]
    assert task.priority == Priority.HIGH


def test_task_with_dates():
    """Test creating task with various date fields."""
    due = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
    scheduled = datetime(2024, 1, 20, 9, 0, 0, tzinfo=timezone.utc)

    task = Task(
        description="Test task",
        due=due,
        scheduled=scheduled,
    )

    assert task.due == due
    assert task.scheduled == scheduled


def test_task_uuid_preservation():
    """Test that providing UUID preserves it."""
    uuid = UUID("12345678-1234-5678-1234-567812345678")
    task = Task(description="Test task", uuid=uuid)

    assert task.uuid == uuid


def test_task_with_dependencies():
    """Test task with dependencies."""
    dep_uuid = UUID("12345678-1234-5678-1234-567812345678")
    task = Task(description="Test task", depends=[dep_uuid])

    assert task.depends == [dep_uuid]


def test_task_dependencies_from_string():
    """Test parsing dependencies from string."""
    task = Task(description="Test task", depends="12345678-1234-5678-1234-567812345678")

    assert len(task.depends) == 1
    assert task.depends[0] == UUID("12345678-1234-5678-1234-567812345678")


def test_task_with_annotations():
    """Test task with annotations."""
    annotation = Annotation(
        entry=datetime(2024, 1, 15, 14, 0, 0, tzinfo=timezone.utc),
        description="Test note",
    )
    task = Task(description="Test task", annotations=[annotation])

    assert len(task.annotations) == 1
    assert task.annotations[0].description == "Test note"


def test_task_datetime_from_string():
    """Test parsing datetime fields from Taskwarrior strings."""
    task = Task(
        description="Test task",
        entry="20240115T143022Z",
        due="20240201T120000Z",
    )

    assert task.entry == datetime(2024, 1, 15, 14, 30, 22, tzinfo=timezone.utc)
    assert task.due == datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_task_to_taskwarrior():
    """Test exporting task to dict."""
    task = Task(
        description="Test task",
        project="test",
        tags=["tag1"],
        priority=Priority.HIGH,
    )

    data = task.to_taskwarrior()

    assert data["description"] == "Test task"
    assert data["project"] == "test"
    assert data["tags"] == ["tag1"]
    assert data["priority"] == "H"
    assert "uuid" in data
    assert "entry" in data
    assert "modified" in data


def test_task_to_taskwarrior_exclude_none():
    """Test that None fields are excluded from export."""
    task = Task(description="Test task")
    data = task.to_taskwarrior(exclude_none=True)

    assert "due" not in data
    assert "scheduled" not in data
    assert "project" not in data
    assert "priority" not in data


def test_task_export_datetime_format():
    """Test that datetimes are exported in Taskwarrior format."""
    task = Task(
        description="Test task",
        entry=datetime(2024, 1, 15, 14, 30, 22, tzinfo=timezone.utc),
    )

    data = task.to_taskwarrior()
    assert data["entry"] == "20240115T143022Z"


def test_task_export_depends_format():
    """Test that dependencies are exported as comma-separated string."""
    uuid1 = UUID("12345678-1234-5678-1234-567812345678")
    uuid2 = UUID("87654321-4321-8765-4321-876543218765")
    task = Task(description="Test task", depends=[uuid1, uuid2])

    data = task.to_taskwarrior()
    assert data["depends"] == "12345678-1234-5678-1234-567812345678,87654321-4321-8765-4321-876543218765"


def test_task_export_empty_depends():
    """Test that empty depends list is excluded."""
    task = Task(description="Test task", depends=[])
    data = task.to_taskwarrior(exclude_none=True)

    assert "depends" not in data


def test_task_core_field_constants():
    """Ensure core field constants match core_field_names."""
    expected = {
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

    assert Task.CORE_FIELDS == expected
    assert Task.core_field_names() == expected


def test_task_get_udas_excludes_core_and_computed():
    """Ensure UDAs exclude core and computed Taskwarrior fields."""
    task = Task(description="Test task", custom="value", id=5, urgency=12.5)

    assert task.get_udas() == {"custom": "value"}
