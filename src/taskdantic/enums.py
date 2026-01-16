# src/taskdantic/enums.py
from __future__ import annotations

from enum import Enum


class Status(str, Enum):
    """Task status values used by Taskwarrior."""

    PENDING = "pending"
    COMPLETED = "completed"
    DELETED = "deleted"
    RECURRING = "recurring"
    WAITING = "waiting"


class Priority(str, Enum):
    """Task priority levels."""

    HIGH = "H"
    MEDIUM = "M"
    LOW = "L"
