# src/taskdantic/utils.py

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from taskdantic.exceptions import ValidationError
from taskdantic.models import Task


def taskwarrior_datetime_serializer(dt: Optional[datetime]) -> Optional[str]:
    """Serialize datetime to Taskwarrior format (20260115T120000Z)."""
    if dt is None:
        return None
    # Ensure UTC timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y%m%dT%H%M%SZ")


def taskwarrior_datetime_validator(value: Any) -> Optional[datetime]:
    """Parse Taskwarrior datetime format to datetime object."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        # Ensure UTC timezone
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    # Parse Taskwarrior format: 20260115T120000Z
    if isinstance(value, str):
        try:
            dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            # Try ISO format as fallback
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt.astimezone(timezone.utc)
            except ValueError as e:
                raise ValueError(f"Invalid datetime format: {value}") from e

    raise TypeError(f"Expected str or datetime, got {type(value)}")


def duration_serializer(duration: Optional[timedelta]) -> Optional[str]:
    """Serialize timedelta to Taskwarrior duration format (P1D, PT2H30M)."""
    if duration is None:
        return None

    total_seconds = int(duration.total_seconds())
    if total_seconds < 0:
        raise ValueError("Duration must be positive")

    days = total_seconds // 86400
    remaining = total_seconds % 86400
    hours = remaining // 3600
    remaining = remaining % 3600
    minutes = remaining // 60
    seconds = remaining % 60

    parts = []
    if days > 0:
        parts.append(f"{days}D")

    time_parts = []
    if hours > 0:
        time_parts.append(f"{hours}H")
    if minutes > 0:
        time_parts.append(f"{minutes}M")
    if seconds > 0:
        time_parts.append(f"{seconds}S")

    if not parts and not time_parts:
        return "PT0S"

    result = "P" + "".join(parts)
    if time_parts:
        result += "T" + "".join(time_parts)

    return result


def duration_validator(value: Any) -> Optional[timedelta]:
    """Parse Taskwarrior duration format to timedelta."""
    if value is None or value == "":
        return None
    if isinstance(value, timedelta):
        return value

    if not isinstance(value, str):
        raise TypeError(f"Expected str or timedelta, got {type(value)}")

    # Parse ISO 8601 duration format: P[n]D[T[n]H[n]M[n]S]
    pattern = r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$"
    match = re.match(pattern, value)

    if not match:
        raise ValueError(f"Invalid duration format: {value}")

    days = int(match.group(1)) if match.group(1) else 0
    hours = int(match.group(2)) if match.group(2) else 0
    minutes = int(match.group(3)) if match.group(3) else 0
    seconds = int(match.group(4)) if match.group(4) else 0

    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


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
    """Format filter specification for task command."""
    if isinstance(filter_spec, str):
        return filter_spec

    parts = []
    for key, value in filter_spec.items():
        if value is None:
            continue
        if isinstance(value, bool):
            parts.append(f"{key}:{str(value).lower()}")
        elif isinstance(value, list):
            for item in value:
                parts.append(f"{key}:{item}")
        else:
            parts.append(f"{key}:{value}")

    return " ".join(parts)
