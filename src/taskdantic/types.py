# src/taskdantic/types.py

from __future__ import annotations

from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """Taskwarrior task status values."""

    PENDING = "pending"
    COMPLETED = "completed"
    DELETED = "deleted"
    WAITING = "waiting"
    RECURRING = "recurring"


class Priority(str, Enum):
    """Task priority levels."""

    HIGH = "H"
    MEDIUM = "M"
    LOW = "L"


TaskDict = dict[str, Any]
TaskFilter = str | dict[str, Any]
