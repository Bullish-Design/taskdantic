# src/taskdantic/services.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from taskdantic.enums import Status
from taskdantic.models import Annotation, Task, _utc_now


class TaskService:
    """Service layer for task operations."""

    def complete(self, task: Task) -> Task:
        """Mark task as completed."""
        if task.status == Status.DELETED:
            raise ValueError("Cannot complete deleted task")
        if task.status == Status.COMPLETED:
            raise ValueError("Task is already completed")

        now = _utc_now()
        task.status = Status.COMPLETED
        task.end = now
        task.modified = now
        return task

    def start(self, task: Task) -> Task:
        """Start the task by setting start timestamp."""
        if task.status != Status.PENDING:
            raise ValueError(f"Cannot start task with status: {task.status.value}")
        if task.start is not None:
            raise ValueError("Task is already started")

        now = _utc_now()
        task.start = now
        task.modified = now
        return task

    def stop(self, task: Task) -> Task:
        """Stop the task by clearing start timestamp."""
        if task.start is None:
            raise ValueError("Task is not started")

        task.start = None
        task.modified = _utc_now()
        return task

    def delete(self, task: Task) -> Task:
        """Mark task as deleted."""
        if task.status == Status.DELETED:
            raise ValueError("Task is already deleted")

        now = _utc_now()
        task.status = Status.DELETED
        task.end = now
        task.modified = now
        return task

    def add_dependency(self, task: Task, dependency: Task | UUID) -> Task:
        """Add a task dependency."""
        uuid_to_add = dependency.uuid if isinstance(dependency, Task) else dependency
        if uuid_to_add == task.uuid:
            raise ValueError("Task cannot depend on itself")
        if uuid_to_add not in task.depends:
            task.depends.append(uuid_to_add)
            task.modified = _utc_now()
        return task

    def remove_dependency(self, task: Task, dependency: Task | UUID) -> Task:
        """Remove a task dependency."""
        uuid_to_remove = dependency.uuid if isinstance(dependency, Task) else dependency
        if uuid_to_remove in task.depends:
            task.depends.remove(uuid_to_remove)
            task.modified = _utc_now()
        return task

    def annotate(self, task: Task, description: str, entry: datetime | None = None) -> Annotation:
        """Add an annotation to the task."""
        annotation = Annotation(
            entry=entry if entry is not None else _utc_now(),
            description=description,
        )
        task.annotations.append(annotation)
        task.modified = _utc_now()
        return annotation

    def tag(self, task: Task, tag: str) -> Task:
        """Add a tag to the task."""
        if tag not in task.tags:
            task.tags.append(tag)
            task.modified = _utc_now()
        return task

    def untag(self, task: Task, tag: str) -> Task:
        """Remove a tag from the task."""
        if tag in task.tags:
            task.tags.remove(tag)
            task.modified = _utc_now()
        return task
