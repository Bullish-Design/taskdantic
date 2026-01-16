# tests/unit/test_models.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from taskdantic.models import Annotation, Task
from taskdantic.types import Priority, TaskStatus


@pytest.mark.unit
class TestTaskModel:
    """Test Task model validation and serialization."""

    def test_minimal_task_creation(self) -> None:
        """Test creating task with only required fields."""
        task = Task(description="Test task")
        assert task.description == "Test task"
        assert task.uuid is None
        assert task.status == TaskStatus.PENDING
        assert task.tags == []
        assert task.annotations == []

    def test_complete_task_creation(self) -> None:
        """Test creating task with all standard fields."""
        task_data = {
            "description": "Complete task",
            "uuid": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
            "status": "pending",
            "project": "test_project",
            "priority": "H",
            "tags": ["urgent", "important"],
            "entry": "2026-01-15T10:00:00Z",
            "due": "2026-01-22T10:00:00Z",
        }
        task = Task.model_validate(task_data)

        assert task.description == "Complete task"
        assert isinstance(task.uuid, UUID)
        assert task.status == TaskStatus.PENDING
        assert task.project == "test_project"
        assert task.priority == Priority.HIGH
        assert set(task.tags) == {"urgent", "important"}
        assert isinstance(task.entry, datetime)
        assert isinstance(task.due, datetime)

    def test_invalid_description_type(self) -> None:
        """Test that invalid description type raises ValidationError."""
        with pytest.raises(ValidationError):
            Task(description=123)  # type: ignore

    def test_empty_description(self) -> None:
        """Test that empty description raises ValidationError."""
        with pytest.raises(ValidationError):
            Task(description="")

    def test_invalid_uuid_format(self) -> None:
        """Test that invalid UUID format raises ValidationError."""
        with pytest.raises(ValidationError):
            Task(description="Test", uuid="not-a-uuid")

    def test_uuid_string_conversion(self) -> None:
        """Test that UUID string is converted to UUID object."""
        task = Task(description="Test", uuid="a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d")
        assert isinstance(task.uuid, UUID)
        assert str(task.uuid) == "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d"

    def test_invalid_priority(self) -> None:
        """Test that invalid priority raises ValidationError."""
        with pytest.raises(ValidationError):
            Task(description="Test", priority="X")  # type: ignore

    def test_invalid_status(self) -> None:
        """Test that invalid status raises ValidationError."""
        with pytest.raises(ValidationError):
            Task(description="Test", status="invalid")  # type: ignore

    def test_date_parsing(self) -> None:
        """Test that date strings are parsed correctly."""
        task = Task(
            description="Test",
            entry="2026-01-15T10:00:00Z",
            due="2026-01-22T12:30:00Z",
        )
        assert isinstance(task.entry, datetime)
        assert isinstance(task.due, datetime)
        assert task.entry.year == 2026
        assert task.due.day == 22

    def test_model_dump(self) -> None:
        """Test model serialization."""
        task = Task(
            description="Test task",
            project="work",
            priority=Priority.HIGH,
            tags=["urgent"],
        )
        data = task.model_dump(exclude_none=True)

        assert data["description"] == "Test task"
        assert data["project"] == "work"
        assert data["priority"] == "H"
        assert data["tags"] == ["urgent"]
        assert "uuid" not in data

    def test_model_dump_with_dates(self) -> None:
        """Test model serialization with datetime fields."""
        task = Task(
            description="Test",
            entry=datetime(2026, 1, 15, 10, 0, 0),
            due=datetime(2026, 1, 22, 12, 30, 0),
        )
        data = task.model_dump()

        assert isinstance(data["entry"], datetime)
        assert isinstance(data["due"], datetime)

    def test_tags_default_empty_list(self) -> None:
        """Test that tags defaults to empty list."""
        task = Task(description="Test")
        assert task.tags == []
        assert isinstance(task.tags, list)

    def test_annotations_default_empty_list(self) -> None:
        """Test that annotations defaults to empty list."""
        task = Task(description="Test")
        assert task.annotations == []
        assert isinstance(task.annotations, list)

    def test_model_extra_for_udas(self) -> None:
        """Test that UDAs are stored in model_extra."""
        task_data = {
            "description": "Test",
            "estimate": 5,
            "complexity": "high",
        }
        task = Task.model_validate(task_data)

        assert task.model_extra is not None
        assert task.model_extra.get("estimate") == 5
        assert task.model_extra.get("complexity") == "high"

    def test_optional_fields_can_be_none(self) -> None:
        """Test that optional fields accept None."""
        task = Task(
            description="Test",
            project=None,
            priority=None,
            due=None,
        )
        assert task.project is None
        assert task.priority is None
        assert task.due is None


@pytest.mark.unit
class TestAnnotationModel:
    """Test Annotation model."""

    def test_annotation_creation(self) -> None:
        """Test creating annotation."""
        annotation = Annotation(
            entry=datetime(2026, 1, 15, 10, 0, 0),
            description="Test annotation",
        )
        assert isinstance(annotation.entry, datetime)
        assert annotation.description == "Test annotation"

    def test_annotation_from_dict(self) -> None:
        """Test creating annotation from dict."""
        data = {
            "entry": "2026-01-15T10:00:00Z",
            "description": "Annotation text",
        }
        annotation = Annotation.model_validate(data)
        assert isinstance(annotation.entry, datetime)
        assert annotation.description == "Annotation text"

    def test_annotation_invalid_entry(self) -> None:
        """Test that invalid entry raises ValidationError."""
        with pytest.raises(ValidationError):
            Annotation(entry="not-a-date", description="Test")  # type: ignore

    def test_annotation_missing_description(self) -> None:
        """Test that missing description raises ValidationError."""
        with pytest.raises(ValidationError):
            Annotation(entry=datetime.now())  # type: ignore


@pytest.mark.unit
class TestPriorityEnum:
    """Test Priority enum."""

    def test_priority_values(self) -> None:
        """Test all priority enum values."""
        assert Priority.HIGH.value == "H"
        assert Priority.MEDIUM.value == "M"
        assert Priority.LOW.value == "L"

    def test_priority_from_string(self) -> None:
        """Test creating priority from string."""
        assert Priority("H") == Priority.HIGH
        assert Priority("M") == Priority.MEDIUM
        assert Priority("L") == Priority.LOW

    def test_invalid_priority_value(self) -> None:
        """Test that invalid priority value raises ValueError."""
        with pytest.raises(ValueError):
            Priority("X")


@pytest.mark.unit
class TestTaskStatusEnum:
    """Test TaskStatus enum."""

    def test_status_values(self) -> None:
        """Test all status enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.DELETED.value == "deleted"
        assert TaskStatus.WAITING.value == "waiting"
        assert TaskStatus.RECURRING.value == "recurring"

    def test_status_from_string(self) -> None:
        """Test creating status from string."""
        assert TaskStatus("pending") == TaskStatus.PENDING
        assert TaskStatus("completed") == TaskStatus.COMPLETED
        assert TaskStatus("deleted") == TaskStatus.DELETED

    def test_invalid_status_value(self) -> None:
        """Test that invalid status value raises ValueError."""
        with pytest.raises(ValueError):
            TaskStatus("invalid")


@pytest.mark.unit
class TestTaskWithAnnotations:
    """Test Task model with annotations."""

    def test_task_with_annotations(self) -> None:
        """Test task with multiple annotations."""
        task_data = {
            "description": "Test task",
            "annotations": [
                {
                    "entry": "2026-01-15T10:00:00Z",
                    "description": "First annotation",
                },
                {
                    "entry": "2026-01-15T11:00:00Z",
                    "description": "Second annotation",
                },
            ],
        }
        task = Task.model_validate(task_data)

        assert len(task.annotations) == 2
        assert all(isinstance(a, Annotation) for a in task.annotations)
        assert task.annotations[0].description == "First annotation"
        assert task.annotations[1].description == "Second annotation"

    def test_task_annotation_validation(self) -> None:
        """Test that invalid annotations raise ValidationError."""
        task_data = {
            "description": "Test task",
            "annotations": [
                {"entry": "invalid-date", "description": "Test"},
            ],
        }
        with pytest.raises(ValidationError):
            Task.model_validate(task_data)
