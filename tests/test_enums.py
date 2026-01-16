# tests/test_enums.py
from __future__ import annotations

import pytest

from taskdantic.enums import Priority, Status


def test_status_values():
    """Test Status enum has expected values."""
    assert Status.PENDING.value == "pending"
    assert Status.COMPLETED.value == "completed"
    assert Status.DELETED.value == "deleted"
    assert Status.RECURRING.value == "recurring"
    assert Status.WAITING.value == "waiting"


def test_priority_values():
    """Test Priority enum has expected values."""
    assert Priority.HIGH.value == "H"
    assert Priority.MEDIUM.value == "M"
    assert Priority.LOW.value == "L"


def test_status_from_string():
    """Test Status can be created from string."""
    assert Status("pending") == Status.PENDING
    assert Status("completed") == Status.COMPLETED


def test_priority_from_string():
    """Test Priority can be created from string."""
    assert Priority("H") == Priority.HIGH
    assert Priority("M") == Priority.MEDIUM


def test_invalid_status():
    """Test invalid status raises ValueError."""
    with pytest.raises(ValueError):
        Status("invalid")


def test_invalid_priority():
    """Test invalid priority raises ValueError."""
    with pytest.raises(ValueError):
        Priority("X")
