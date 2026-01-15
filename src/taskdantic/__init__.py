# src/taskdantic/__init__.py

from __future__ import annotations

from taskdantic.config import TaskRcParser
from taskdantic.exceptions import (
    ConfigError,
    TaskNotFoundError,
    TaskWarriorCommandError,
    TaskWarriorError,
    TaskWarriorNotInstalledError,
    ValidationError,
)
from taskdantic.models import Annotation, Task, TaskConfig, UDADefinition
from taskdantic.types import Priority, TaskStatus
from taskdantic.warrior import TaskWarrior

__version__ = "0.1.0"

__all__ = [
    "Annotation",
    "ConfigError",
    "Priority",
    "Task",
    "TaskConfig",
    "TaskNotFoundError",
    "TaskRcParser",
    "TaskStatus",
    "TaskWarrior",
    "TaskWarriorCommandError",
    "TaskWarriorError",
    "TaskWarriorNotInstalledError",
    "UDADefinition",
    "ValidationError",
]
