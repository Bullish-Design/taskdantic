# tests/test_utils.py
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from taskdantic.utils import datetime_to_taskwarrior, taskwarrior_to_datetime


def test_taskwarrior_to_datetime():
    """Test parsing Taskwarrior timestamp format."""
    result = taskwarrior_to_datetime("20240115T143022Z")
    expected = datetime(2024, 1, 15, 14, 30, 22, tzinfo=timezone.utc)
    assert result == expected


def test_datetime_to_taskwarrior():
    """Test serializing datetime to Taskwarrior format."""
    dt = datetime(2024, 1, 15, 14, 30, 22, tzinfo=timezone.utc)
    result = datetime_to_taskwarrior(dt)
    assert result == "20240115T143022Z"


def test_datetime_roundtrip():
    """Test datetime conversion in both directions."""
    original = "20240115T143022Z"
    dt = taskwarrior_to_datetime(original)
    result = datetime_to_taskwarrior(dt)
    assert result == original


def test_datetime_to_taskwarrior_naive():
    """Test that naive datetimes are treated as UTC."""
    dt = datetime(2024, 1, 15, 14, 30, 22)
    result = datetime_to_taskwarrior(dt)
    assert result == "20240115T143022Z"


def test_datetime_to_taskwarrior_timezone_conversion():
    """Test that non-UTC timezones are converted to UTC."""
    from datetime import timedelta

    dt = datetime(2024, 1, 15, 14, 30, 22, tzinfo=timezone(timedelta(hours=5)))
    result = datetime_to_taskwarrior(dt)
    assert result == "20240115T093022Z"
