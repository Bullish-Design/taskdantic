# src/taskdantic/exceptions.py

from __future__ import annotations


class TaskWarriorError(Exception):
    """Base exception for all taskdantic errors."""


class TaskNotFoundError(TaskWarriorError):
    """Task does not exist."""


class TaskWarriorNotInstalledError(TaskWarriorError):
    """Taskwarrior executable not found."""


class TaskWarriorCommandError(TaskWarriorError):
    """Taskwarrior command execution failed."""


class ConfigError(TaskWarriorError):
    """Configuration file parsing error."""


class ValidationError(TaskWarriorError):
    """Task validation error."""
