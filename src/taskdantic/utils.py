# src/taskdantic/utils.py

from __future__ import annotations

import json
from typing import Any

from taskdantic.exceptions import ValidationError
from taskdantic.models import Task


def parse_task_export(json_output: str) -> list[Task]:
    """Parse JSON output from 'task export' command into Task objects."""
    if not json_output or json_output.strip() == "":
        return []

    try:
        data = json.loads(json_output)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON from task export: {e}") from e

    if not isinstance(data, list):
        raise ValidationError("Expected JSON array from task export")

    tasks = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            task = Task.model_validate(item)
            tasks.append(task)
        except Exception as e:
            raise ValidationError(f"Failed to parse task: {e}") from e

    return tasks


def task_to_json(task: Task) -> str:
    """Convert Task to JSON string for 'task import'."""
    data = task.model_dump(
        mode="json",
        exclude_none=True,
        exclude={"id", "urgency"},
        by_alias=True,
    )
    return json.dumps(data)


def format_filter(filter_spec: str | dict[str, Any]) -> str:
    """Format filter specification for task command.

    Args:
        filter_spec: Either a string filter or dict of key-value pairs

    Returns:
        Formatted filter string for task command

    Notes:
        - Tags are prefixed with + (e.g., {"tags": "urgent"} -> "+urgent")
        - None values output as "key:" (e.g., {"project": None} -> "project:")
    """
    if isinstance(filter_spec, str):
        return filter_spec

    parts = []
    for key, value in filter_spec.items():
        # Handle None - output as "key:" to clear the field
        if value is None:
            parts.append(f"{key}:")
            continue

        # Handle tags specially - prefix with +
        if key == "tags":
            if isinstance(value, list):
                for tag in value:
                    parts.append(f"+{tag}")
            else:
                parts.append(f"+{value}")
            continue

        # Handle other values
        if isinstance(value, bool):
            parts.append(f"{key}:{str(value).lower()}")
        elif isinstance(value, list):
            for item in value:
                parts.append(f"{key}:{item}")
        else:
            parts.append(f"{key}:{value}")

    return " ".join(parts)
