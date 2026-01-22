# src/taskdantic/__init__.py
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from taskdantic.enums import Priority, Status
from taskdantic.models import Annotation, Task
from taskdantic.services import TaskService
from taskdantic.task_types import TWDatetime, TWDuration, UUIDList
from taskdantic.uda import uda
from taskdantic.uda_mixins import AgileUDAMixin, BugTrackingUDAMixin, FinanceUDAMixin, UDAMixin
from taskdantic.uda_registry import UDARegistry
from taskdantic.utils import export_tasks, load_tasks


try:
    __version__ = version("taskdantic")
except PackageNotFoundError:  # pragma: no cover - fallback for editable installs without metadata
    __version__ = "0.1.1"

__all__ = [
    "Task",
    "Annotation",
    "Status",
    "Priority",
    "TWDatetime",
    "TWDuration",
    "UUIDList",
    "TaskService",
    "UDAMixin",
    "AgileUDAMixin",
    "BugTrackingUDAMixin",
    "FinanceUDAMixin",
    "UDARegistry",
    "uda",
    "load_tasks",
    "export_tasks",
]
