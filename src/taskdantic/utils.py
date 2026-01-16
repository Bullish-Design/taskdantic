# src/taskdantic/utils.py
from __future__ import annotations

from datetime import datetime, timezone


def taskwarrior_to_datetime(tw_timestamp: str) -> datetime:
    """Convert Taskwarrior timestamp (YYYYMMDDTHHmmssZ) to datetime object."""
    return datetime.strptime(tw_timestamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)


def datetime_to_taskwarrior(dt: datetime) -> str:
    """Convert datetime object to Taskwarrior timestamp format."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
