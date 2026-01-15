# tests/unit/test_utils.py
from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

import pytest

from taskdantic.models import Priority, Task, TaskStatus
from taskdantic.utils import format_filter, parse_task_export, task_to_json


@pytest.mark.unit
class TestParseTaskExport:
    """Test parse_task_export function."""

    def test_parse_empty_export(self) -> None:
        """Test parsing empty export returns empty list."""
        result = parse_task_export("")
        assert result == []

        result = parse_task_export("[]")
        assert result == []

    def test_parse_single_task(self) -> None:
        """Test parsing single task from export."""
        export_data = json.dumps([{
            "description": "Test task",
            "uuid": str(uuid4()),
            "status": "pending",
            "entry": "20260115T100000Z",
        }])

        tasks = parse_task_export(export_data)
        assert len(tasks) == 1
        assert tasks[0].description == "Test task"
        assert tasks[0].status == TaskStatus.PENDING

    def test_parse_multiple_tasks(self) -> None:
        """Test parsing multiple tasks from export."""
        export_data = json.dumps([
            {
                "description": "Task 1",
                "uuid": str(uuid4()),
                "status": "pending",
                "entry": "20260115T100000Z",
            },
            {
                "description": "Task 2",
                "uuid": str(uuid4()),
                "status": "completed",
                "entry": "20260115T110000Z",
                "end": "20260115T120000Z",
            },
        ])

        tasks = parse_task_export(export_data)
        assert len(tasks) == 2
        assert tasks[0].description == "Task 1"
        assert tasks[1].description == "Task 2"
        assert tasks[1].status == TaskStatus.COMPLETED

    def test_parse_task_with_tags(self) -> None:
        """Test parsing task with tags."""
        export_data = json.dumps([{
            "description": "Test task",
            "uuid": str(uuid4()),
            "status": "pending",
            "entry": "20260115T100000Z",
            "tags": ["urgent", "important"],
        }])

        tasks = parse_task_export(export_data)
        assert len(tasks[0].tags) == 2
        assert set(tasks[0].tags) == {"urgent", "important"}

    def test_parse_task_with_annotations(self) -> None:
        """Test parsing task with annotations."""
        export_data = json.dumps([{
            "description": "Test task",
            "uuid": str(uuid4()),
            "status": "pending",
            "entry": "20260115T100000Z",
            "annotations": [
                {
                    "entry": "20260115T110000Z",
                    "description": "Annotation text",
                },
            ],
        }])

        tasks = parse_task_export(export_data)
        assert len(tasks[0].annotations) == 1
        assert tasks[0].annotations[0].description == "Annotation text"

    def test_parse_task_with_udas(self) -> None:
        """Test parsing task with user-defined attributes."""
        export_data = json.dumps([{
            "description": "Test task",
            "uuid": str(uuid4()),
            "status": "pending",
            "entry": "20260115T100000Z",
            "estimate": 5,
            "complexity": "high",
        }])

        tasks = parse_task_export(export_data)
        assert tasks[0].model_extra is not None
        assert tasks[0].model_extra.get("estimate") == 5
        assert tasks[0].model_extra.get("complexity") == "high"

    def test_parse_invalid_json(self) -> None:
        """Test that invalid JSON raises ValueError."""
        with pytest.raises((ValueError, json.JSONDecodeError)):
            parse_task_export("not valid json")

    def test_parse_task_with_all_fields(self) -> None:
        """Test parsing task with all standard fields."""
        task_uuid = str(uuid4())
        export_data = json.dumps([{
            "description": "Complete task",
            "uuid": task_uuid,
            "status": "pending",
            "entry": "20260115T100000Z",
            "project": "work",
            "priority": "H",
            "tags": ["urgent"],
            "due": "20260122T100000Z",
            "modified": "20260115T110000Z",
        }])

        tasks = parse_task_export(export_data)
        task = tasks[0]
        assert task.description == "Complete task"
        assert str(task.uuid) == task_uuid
        assert task.project == "work"
        assert task.priority == Priority.HIGH
        assert task.tags == ["urgent"]


@pytest.mark.unit
class TestTaskToJson:
    """Test task_to_json function."""

    def test_minimal_task_to_json(self) -> None:
        """Test converting minimal task to JSON."""
        task = Task(description="Test task")
        json_str = task_to_json(task)

        data = json.loads(json_str)
        assert data["description"] == "Test task"
        assert data["status"] == "pending"
        assert "uuid" not in data

    def test_complete_task_to_json(self) -> None:
        """Test converting complete task to JSON."""
        task = Task(
            description="Complete task",
            uuid=uuid4(),
            project="work",
            priority=Priority.HIGH,
            tags=["urgent", "important"],
        )
        json_str = task_to_json(task)

        data = json.loads(json_str)
        assert data["description"] == "Complete task"
        assert data["project"] == "work"
        assert data["priority"] == "H"
        assert set(data["tags"]) == {"urgent", "important"}

    def test_task_with_dates_to_json(self) -> None:
        """Test converting task with dates to JSON."""
        task = Task(
            description="Test task",
            entry=datetime(2026, 1, 15, 10, 0, 0),
            due=datetime(2026, 1, 22, 12, 0, 0),
        )
        json_str = task_to_json(task)

        data = json.loads(json_str)
        assert "entry" in data
        assert "due" in data

    def test_task_with_annotations_to_json(self) -> None:
        """Test converting task with annotations to JSON."""
        task_data = {
            "description": "Test task",
            "annotations": [
                {
                    "entry": "20260115T100000Z",
                    "description": "Annotation text",
                },
            ],
        }
        task = Task.model_validate(task_data)
        json_str = task_to_json(task)

        data = json.loads(json_str)
        assert "annotations" in data
        assert len(data["annotations"]) == 1
        assert data["annotations"][0]["description"] == "Annotation text"

    def test_task_with_udas_to_json(self) -> None:
        """Test converting task with UDAs to JSON."""
        task_data = {
            "description": "Test task",
            "estimate": 5,
            "complexity": "high",
        }
        task = Task.model_validate(task_data)
        json_str = task_to_json(task)

        data = json.loads(json_str)
        assert data["estimate"] == 5
        assert data["complexity"] == "high"

    def test_none_values_excluded(self) -> None:
        """Test that None values are excluded from JSON."""
        task = Task(
            description="Test task",
            project=None,
            priority=None,
        )
        json_str = task_to_json(task)

        data = json.loads(json_str)
        assert "project" not in data
        assert "priority" not in data


@pytest.mark.unit
class TestFormatFilter:
    """Test format_filter function."""

    def test_empty_string_filter(self) -> None:
        """Test empty string returns empty string."""
        assert format_filter("") == ""

    def test_simple_string_filter(self) -> None:
        """Test simple string filter passes through."""
        assert format_filter("status:pending") == "status:pending"

    def test_complex_string_filter(self) -> None:
        """Test complex string filter passes through."""
        filter_str = "project:work status:pending priority:H"
        assert format_filter(filter_str) == filter_str

    def test_dict_filter_single_key(self) -> None:
        """Test dict filter with single key."""
        result = format_filter({"status": "pending"})
        assert result == "status:pending"

    def test_dict_filter_multiple_keys(self) -> None:
        """Test dict filter with multiple keys."""
        filter_dict = {
            "status": "pending",
            "project": "work",
            "priority": "H",
        }
        result = format_filter(filter_dict)

        # Check all parts are present
        assert "status:pending" in result
        assert "project:work" in result
        assert "priority:H" in result

    def test_dict_filter_with_tags(self) -> None:
        """Test dict filter with tags."""
        result = format_filter({"tags": "urgent"})
        assert result == "+urgent"

    def test_dict_filter_with_none_value(self) -> None:
        """Test dict filter with None value for clearing."""
        result = format_filter({"project": None})
        assert "project:" in result

    def test_empty_dict_filter(self) -> None:
        """Test empty dict returns empty string."""
        assert format_filter({}) == ""

    def test_filter_with_special_chars(self) -> None:
        """Test filter with special characters."""
        filter_str = "description.contains:test-value"
        assert format_filter(filter_str) == filter_str
