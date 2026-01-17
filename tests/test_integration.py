# tests/test_integration.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

from taskdantic import Priority, Status, Task
from taskdantic.models import Annotation


def test_roundtrip_minimal_task():
    """Test full roundtrip: create → export → parse."""
    original = Task(description="Minimal task")

    exported = original.to_taskwarrior()
    parsed = Task.from_taskwarrior(exported)

    assert parsed.description == original.description
    assert parsed.uuid == original.uuid
    assert parsed.status == original.status


def test_roundtrip_complex_task():
    """Test roundtrip with all common fields populated."""
    original = Task(
        description="Complex task",
        status=Status.PENDING,
        project="test_project",
        tags=["urgent", "work"],
        priority=Priority.HIGH,
        due=datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
        scheduled=datetime(2024, 1, 20, 9, 0, 0, tzinfo=timezone.utc),
        depends=[UUID("12345678-1234-5678-1234-567812345678")],
        annotations=[
            Annotation(
                entry=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                description="First note",
            )
        ],
    )

    exported = original.to_taskwarrior()
    parsed = Task.from_taskwarrior(exported)

    assert parsed.description == original.description
    assert parsed.project == original.project
    assert parsed.tags == original.tags
    assert parsed.priority == original.priority
    assert parsed.due == original.due
    assert parsed.scheduled == original.scheduled
    assert parsed.depends == original.depends
    assert len(parsed.annotations) == 1
    assert parsed.annotations[0].description == "First note"


def test_from_taskwarrior_with_id_field():
    """Test parsing Taskwarrior export that includes 'id' field."""
    data = {
        "id": 42,
        "uuid": "12345678-1234-5678-1234-567812345678",
        "description": "Test task",
        "status": "pending",
        "entry": "20240115T143022Z",
        "modified": "20240115T143022Z",
    }

    task = Task.from_taskwarrior(data)

    assert task.description == "Test task"
    assert not hasattr(task, "id")


def test_from_taskwarrior_with_urgency_field():
    """Test parsing Taskwarrior export that includes 'urgency' field."""
    data = {
        "uuid": "12345678-1234-5678-1234-567812345678",
        "description": "Test task",
        "status": "pending",
        "urgency": 5.2,
        "entry": "20240115T143022Z",
        "modified": "20240115T143022Z",
    }

    task = Task.from_taskwarrior(data)

    assert task.description == "Test task"
    assert not hasattr(task, "urgency")


def test_from_taskwarrior_empty_tags():
    """Test parsing task with empty tags list."""
    data = {
        "uuid": "12345678-1234-5678-1234-567812345678",
        "description": "Test task",
        "status": "pending",
        "tags": [],
        "entry": "20240115T143022Z",
        "modified": "20240115T143022Z",
    }

    task = Task.from_taskwarrior(data)
    assert task.tags == []


def test_from_taskwarrior_completed_task():
    """Test parsing a completed task with end timestamp."""
    data = {
        "uuid": "12345678-1234-5678-1234-567812345678",
        "description": "Completed task",
        "status": "completed",
        "entry": "20240115T143022Z",
        "modified": "20240116T100000Z",
        "end": "20240116T100000Z",
    }

    task = Task.from_taskwarrior(data)

    assert task.status == Status.COMPLETED
    assert task.end == datetime(2024, 1, 16, 10, 0, 0, tzinfo=timezone.utc)


def test_from_taskwarrior_waiting_task():
    """Test parsing a waiting task with wait timestamp."""
    data = {
        "uuid": "12345678-1234-5678-1234-567812345678",
        "description": "Waiting task",
        "status": "waiting",
        "entry": "20240115T143022Z",
        "modified": "20240115T143022Z",
        "wait": "20240201T090000Z",
    }

    task = Task.from_taskwarrior(data)

    assert task.status == Status.WAITING
    assert task.wait == datetime(2024, 2, 1, 9, 0, 0, tzinfo=timezone.utc)


def test_multiple_tasks_batch_processing():
    """Test processing multiple tasks in batch."""
    tasks_data = [
        {
            "uuid": "12345678-1234-5678-1234-567812345678",
            "description": "Task 1",
            "status": "pending",
            "entry": "20240115T143022Z",
            "modified": "20240115T143022Z",
        },
        {
            "uuid": "87654321-4321-8765-4321-876543218765",
            "description": "Task 2",
            "status": "completed",
            "entry": "20240114T120000Z",
            "modified": "20240115T100000Z",
            "end": "20240115T100000Z",
        },
    ]

    tasks = [Task.from_taskwarrior(data) for data in tasks_data]

    assert len(tasks) == 2
    assert tasks[0].description == "Task 1"
    assert tasks[0].status == Status.PENDING
    assert tasks[1].description == "Task 2"
    assert tasks[1].status == Status.COMPLETED


def test_export_import_preserves_datetime_precision():
    """Test that datetime precision is preserved through export/import cycle."""
    original_time = datetime(2024, 1, 15, 14, 30, 22, tzinfo=timezone.utc)
    task = Task(description="Test", due=original_time)

    exported = task.to_taskwarrior()
    parsed = Task.from_taskwarrior(exported)

    assert parsed.due == original_time
