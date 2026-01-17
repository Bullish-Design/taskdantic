# src/taskdantic/utils.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from taskdantic.models import Task


def taskwarrior_to_datetime(tw_timestamp: str) -> datetime:
    """
    Convert Taskwarrior timestamp (YYYYMMDDTHHmmssZ) to datetime object.

    Args:
        tw_timestamp: Taskwarrior timestamp string

    Returns:
        Timezone-aware datetime in UTC

    Raises:
        ValueError: If timestamp format is invalid
    """
    return datetime.strptime(tw_timestamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)


def datetime_to_taskwarrior(dt: datetime) -> str:
    """
    Convert datetime object to Taskwarrior timestamp format.

    Args:
        dt: Datetime to convert (naive datetimes treated as UTC)

    Returns:
        Taskwarrior timestamp string (YYYYMMDDTHHmmssZ)
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_tasks(json_data: list[dict[str, Any]]) -> list[Task]:
    """
    Load multiple tasks from Taskwarrior export JSON.

    Args:
        json_data: List of task dictionaries from Taskwarrior

    Returns:
        List of validated Task instances

    Example:
        >>> import json
        >>> with open("tasks.json") as f:
        ...     data = json.load(f)
        >>> tasks = load_tasks(data)
    """
    from taskdantic.models import Task

    return [Task.from_taskwarrior(task_data) for task_data in json_data]


def export_tasks(tasks: list[Task], exclude_none: bool = True) -> list[dict[str, Any]]:
    """
    Export multiple tasks to Taskwarrior JSON format.

    Args:
        tasks: List of Task instances to export
        exclude_none: Whether to exclude None values from output

    Returns:
        List of task dictionaries in Taskwarrior format

    Example:
        >>> tasks = [Task(description="Task 1"), Task(description="Task 2")]
        >>> data = export_tasks(tasks)
    """
    return [task.to_taskwarrior(exclude_none=exclude_none) for task in tasks]
