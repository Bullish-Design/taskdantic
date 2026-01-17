# tests/test_service.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

from taskdantic.enums import Status
from taskdantic.models import Task
from taskdantic.services import TaskService


def test_service_complete_updates_end_and_modified():
    service = TaskService()
    task = Task(description="Finish report")
    task.modified = datetime(2000, 1, 1, tzinfo=timezone.utc)

    service.complete(task)

    assert task.status == Status.COMPLETED
    assert task.end is not None
    assert task.modified > datetime(2000, 1, 1, tzinfo=timezone.utc)


def test_service_start_and_stop_updates_timestamps():
    service = TaskService()
    task = Task(description="Start timer")
    task.modified = datetime(2000, 1, 1, tzinfo=timezone.utc)

    service.start(task)

    assert task.start is not None
    assert task.modified > datetime(2000, 1, 1, tzinfo=timezone.utc)

    start_time = task.start
    service.stop(task)

    assert task.start is None
    assert task.modified is not None
    assert start_time is not None


def test_service_delete_sets_deleted_status_and_end():
    service = TaskService()
    task = Task(description="Old task")
    task.modified = datetime(2000, 1, 1, tzinfo=timezone.utc)

    service.delete(task)

    assert task.status == Status.DELETED
    assert task.end is not None
    assert task.modified > datetime(2000, 1, 1, tzinfo=timezone.utc)


def test_service_dependency_operations():
    service = TaskService()
    task = Task(description="Main task")
    dependency_uuid = UUID("12345678-1234-5678-1234-567812345678")

    service.add_dependency(task, dependency_uuid)
    assert dependency_uuid in task.depends

    service.remove_dependency(task, dependency_uuid)
    assert dependency_uuid not in task.depends


def test_service_dependency_rejects_self():
    service = TaskService()
    task = Task(description="Main task")

    with pytest.raises(ValueError, match="depend on itself"):
        service.add_dependency(task, task)
