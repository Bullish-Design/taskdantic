# src/taskdantic/task_types.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from pydantic import BeforeValidator, PlainSerializer

from taskdantic.utils import datetime_to_taskwarrior, taskwarrior_to_datetime


def _parse_tw_datetime(value: str | datetime) -> datetime:
    """Parse Taskwarrior timestamp format or pass through datetime."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return taskwarrior_to_datetime(value)
    raise ValueError(f"Expected str or datetime, got {type(value).__name__}")


def _parse_tw_duration(value: str | int | timedelta) -> timedelta:
    """Parse ISO 8601 duration format, seconds, or pass through timedelta."""
    if isinstance(value, timedelta):
        return value

    if isinstance(value, str):
        if not value.startswith("PT"):
            raise ValueError(
                f"Invalid ISO 8601 duration format: {value!r}. "
                f"Expected format: PT#H#M#S (e.g., 'PT2H30M')"
            )
        return _parse_iso_duration(value)

    if isinstance(value, (int, float)):
        return timedelta(seconds=int(value))

    raise ValueError(f"Expected str, int, or timedelta, got {type(value).__name__}")


def _parse_iso_duration(value: str) -> timedelta:
    """Parse ISO 8601 duration string (PT#H#M#S)."""
    hours = 0
    minutes = 0
    seconds = 0

    remainder = value[2:]  # Remove PT prefix

    if "H" in remainder:
        hours_str, remainder = remainder.split("H", 1)
        hours = int(hours_str)

    if "M" in remainder:
        minutes_str, remainder = remainder.split("M", 1)
        minutes = int(minutes_str)

    if "S" in remainder:
        seconds = int(remainder.replace("S", ""))

    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


def _serialize_tw_duration(value: timedelta) -> str:
    """Serialize timedelta to ISO 8601 duration string."""
    total_seconds = int(value.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    parts = []
    if hours:
        parts.append(f"{hours}H")
    if minutes:
        parts.append(f"{minutes}M")
    if seconds:
        parts.append(f"{seconds}S")

    return "PT" + "".join(parts) if parts else "PT0S"


def _parse_uuid_list(value: None | str | list[UUID | str]) -> list[UUID]:
    """Parse comma-separated UUID string or list."""
    if value is None:
        return []

    if isinstance(value, list):
        return [UUID(u) if isinstance(u, str) else u for u in value]

    if isinstance(value, str):
        if not value.strip():
            return []
        return [UUID(u.strip()) for u in value.split(",") if u.strip()]

    raise ValueError(f"Expected None, str, or list, got {type(value).__name__}")


def _serialize_uuid_list(value: list[UUID]) -> str | None:
    """Serialize UUID list to comma-separated string."""
    if not value:
        return None
    return ",".join(str(u) for u in value)


# Public type aliases using Annotated
TWDatetime = Annotated[
    datetime,
    BeforeValidator(_parse_tw_datetime),
    PlainSerializer(datetime_to_taskwarrior, return_type=str),
]

TWDuration = Annotated[
    timedelta,
    BeforeValidator(_parse_tw_duration),
    PlainSerializer(_serialize_tw_duration, return_type=str),
]

UUIDList = Annotated[
    list[UUID],
    BeforeValidator(_parse_uuid_list),
    PlainSerializer(_serialize_uuid_list, return_type=str | None),
]
