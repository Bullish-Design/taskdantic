# src/taskdantic/__init__.py
from __future__ import annotations

from taskdantic.enums import Priority, Status
from taskdantic.models import Annotation, Task
from taskdantic.task_types import TWDatetime, TWDuration, UUIDList
from taskdantic.utils import export_tasks, load_tasks


__version__ = "0.1.0"

__all__ = [
    "Task",
    "Annotation",
    "Status",
    "Priority",
    "TWDatetime",
    "TWDuration",
    "UUIDList",
    "load_tasks",
    "export_tasks",
]


# Optional startup sync: if TASKRC_PATH is set, update taskrc UDAs from code.
from taskdantic.uda_sync import auto_sync_taskrc_from_env as _auto_sync_taskrc_from_env

_auto_sync_taskrc_from_env()
