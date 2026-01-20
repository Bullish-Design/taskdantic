# tests/test_uda_integration.py
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from pydantic import Field, field_validator

from taskdantic import Priority, Status, Task, TWDatetime, TWDuration, UUIDList


class AgileTask(Task):
    """Agile development task."""

    sprint: str | None = None
    points: int = 0
    estimate: TWDuration | None = None
    reviewed: TWDatetime | None = None

    @field_validator("sprint")
    @classmethod
    def validate_sprint(cls, v: str | None) -> str | None:
        if v and not v.startswith("Sprint "):
            return f"Sprint {v}"
        return v


class BugTask(Task):
    """Bug tracking task."""

    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    reported_by: str | None = None
    fixed_in: str | None = None


class DevOpsTask(Task):
    """DevOps deployment task."""

    environment: str | None = Field(default=None, pattern="^(dev|staging|prod)$")
    deployment_time: TWDatetime | None = None
    rollback_safe: bool = True


def test_full_agile_workflow():
    """Test complete agile workflow with task lifecycle."""
    tasks = [
        AgileTask(
            description="Implement OAuth2",
            project="backend",
            tags=["security"],
            priority=Priority.HIGH,
            sprint="23",
            points=8,
            estimate=timedelta(hours=6),
        ),
        AgileTask(
            description="Add user profile",
            project="frontend",
            tags=["feature"],
            priority=Priority.MEDIUM,
            sprint="23",
            points=5,
            estimate=timedelta(hours=4),
        ),
        AgileTask(
            description="Write API docs",
            project="docs",
            tags=["documentation"],
            priority=Priority.LOW,
            sprint="23",
            points=3,
            estimate=timedelta(hours=2),
        ),
    ]

    total_points = sum(t.points for t in tasks)
    total_estimate = sum((t.estimate for t in tasks if t.estimate), timedelta())

    assert total_points == 16
    assert total_estimate == timedelta(hours=12)

    exported_tasks = [t.to_taskwarrior() for t in tasks]
    assert len(exported_tasks) == 3
    assert all("sprint" in t for t in exported_tasks)
    assert all(t["sprint"] == "Sprint 23" for t in exported_tasks)

    imported_tasks = [AgileTask.from_taskwarrior(data) for data in exported_tasks]
    assert len(imported_tasks) == 3
    assert all(t.sprint == "Sprint 23" for t in imported_tasks)


def test_bug_tracking_workflow():
    """Test bug tracking workflow."""
    bug = BugTask(
        description="Login redirects to wrong page",
        project="website",
        tags=["bug", "auth"],
        priority=Priority.HIGH,
        severity="high",
        reported_by="user@example.com",
    )

    assert bug.severity == "high"
    assert bug.status == Status.PENDING

    exported = bug.to_taskwarrior()
    assert exported["severity"] == "high"
    assert exported["reported_by"] == "user@example.com"

    bug.status = Status.COMPLETED
    bug.fixed_in = "v1.2.3"
    bug.end = datetime.now(timezone.utc)

    exported_fixed = bug.to_taskwarrior()
    assert exported_fixed["status"] == "completed"
    assert exported_fixed["fixed_in"] == "v1.2.3"


def test_devops_deployment_workflow():
    """Test DevOps deployment workflow."""
    dev_deploy = DevOpsTask(
        description="Deploy to dev",
        project="platform",
        environment="dev",
        rollback_safe=True,
    )

    staging_deploy = DevOpsTask(
        description="Deploy to staging",
        project="platform",
        environment="staging",
        rollback_safe=True,
    )

    prod_deploy = DevOpsTask(
        description="Deploy to production",
        project="platform",
        environment="prod",
        rollback_safe=False,
    )

    for task in [dev_deploy, staging_deploy, prod_deploy]:
        task.status = Status.COMPLETED
        task.deployment_time = datetime.now(timezone.utc)

    assert dev_deploy.environment == "dev"
    assert staging_deploy.environment == "staging"
    assert prod_deploy.environment == "prod"
    assert all(t.status == Status.COMPLETED for t in [dev_deploy, staging_deploy, prod_deploy])


def test_mixed_task_types_in_project():
    """Test working with multiple task types in same project."""
    tasks: list[Task] = [
        AgileTask(description="Task 1", sprint="Sprint 25", points=5),
        AgileTask(description="Task 2", sprint="Sprint 25", points=8),
        BugTask(description="Bug fix", severity="high"),
        DevOpsTask(description="Deploy", environment="prod"),
    ]

    agile_tasks = [t for t in tasks if isinstance(t, AgileTask)]
    bug_tasks = [t for t in tasks if isinstance(t, BugTask)]
    devops_tasks = [t for t in tasks if isinstance(t, DevOpsTask)]

    assert len(agile_tasks) == 2
    assert len(bug_tasks) == 1
    assert len(devops_tasks) == 1

    sprint_points = sum(t.points for t in agile_tasks)
    assert sprint_points == 13


def test_taskwarrior_import_export_compatibility():
    """Test full compatibility with Taskwarrior JSON format."""
    tw_data = {
        "id": 42,
        "uuid": "12345678-1234-5678-1234-567812345678",
        "description": "Implement feature",
        "status": "pending",
        "entry": "20240115T143022Z",
        "modified": "20240116T100000Z",
        "project": "backend",
        "tags": ["feature", "api"],
        "priority": "H",
        "due": "20240201T120000Z",
        "urgency": 10.5,
        "sprint": "Sprint 23",
        "points": 8,
        "estimate": "PT6H",
    }

    task = AgileTask.from_taskwarrior(tw_data)

    assert task.description == "Implement feature"
    assert task.status == Status.PENDING
    assert task.project == "backend"
    assert task.tags == ["feature", "api"]
    assert task.priority == Priority.HIGH

    assert task.sprint == "Sprint 23"
    assert task.points == 8
    assert task.estimate == timedelta(hours=6)

    assert not hasattr(task, "id")
    assert not hasattr(task, "urgency")

    exported = task.to_taskwarrior()

    assert "id" not in exported
    assert "urgency" not in exported

    assert exported["sprint"] == "Sprint 23"
    assert exported["points"] == 8
    assert exported["estimate"] == "PT6H"


def test_complex_uda_types_integration():
    """Test integration with complex UDA types."""

    class ProjectTask(Task):
        blocked_by: UUIDList | None = None
        reviewed_by: list[str] | None = None
        last_review: TWDatetime | None = None
        time_spent: TWDuration | None = None

    blocker1_uuid = UUID("12345678-1234-5678-1234-567812345678")
    blocker2_uuid = UUID("87654321-4321-8765-4321-876543218765")

    task = ProjectTask(
        description="Implement feature",
        blocked_by=[blocker1_uuid, blocker2_uuid],
        reviewed_by=["alice@example.com", "bob@example.com"],
        last_review=datetime(2024, 1, 20, 10, 0, 0, tzinfo=timezone.utc),
        time_spent=timedelta(hours=4, minutes=30),
    )

    exported = task.to_taskwarrior()

    assert exported["blocked_by"] == f"{blocker1_uuid},{blocker2_uuid}"
    assert exported["last_review"] == "20240120T100000Z"
    assert exported["time_spent"] == "PT4H30M"

    imported = ProjectTask.from_taskwarrior(exported)

    assert imported.blocked_by == [blocker1_uuid, blocker2_uuid]
    assert imported.last_review == datetime(2024, 1, 20, 10, 0, 0, tzinfo=timezone.utc)
    assert imported.time_spent == timedelta(hours=4, minutes=30)


def test_task_status_transitions_with_udas():
    """Test task status transitions with UDA tracking."""
    task = AgileTask(
        description="Feature implementation",
        sprint="Sprint 25",
        points=8,
        estimate=timedelta(hours=6),
    )

    task.status = Status.PENDING
    task.start = datetime.now(timezone.utc)

    task.reviewed = datetime.now(timezone.utc)

    task.status = Status.COMPLETED
    task.end = datetime.now(timezone.utc)

    assert task.status == Status.COMPLETED
    assert task.sprint == "Sprint 25"
    assert task.reviewed is not None
    assert task.start is not None
    assert task.end is not None


def test_batch_operations_with_udas():
    """Test batch operations on tasks with UDAs."""
    tasks = [
        AgileTask(description=f"Task {i}", sprint=f"Sprint {23 + i // 3}", points=(i % 5) + 1)
        for i in range(10)
    ]

    by_sprint: dict[str, list[AgileTask]] = {}
    for task in tasks:
        if task.sprint not in by_sprint:
            by_sprint[task.sprint] = []
        by_sprint[task.sprint].append(task)

    assert len(by_sprint) >= 3

    for sprint, sprint_tasks in by_sprint.items():
        total = sum(t.points for t in sprint_tasks)
        assert total > 0


def test_json_serialization_deserialization():
    """Test JSON serialization and deserialization."""
    task = AgileTask(
        description="JSON test",
        sprint="Sprint 26",
        points=5,
        estimate=timedelta(hours=3),
        reviewed=datetime(2024, 1, 20, 10, 0, 0, tzinfo=timezone.utc),
    )

    exported = task.to_taskwarrior()
    json_str = json.dumps(exported)

    data = json.loads(json_str)
    imported = AgileTask.from_taskwarrior(data)

    assert imported.description == task.description
    assert imported.sprint == task.sprint
    assert imported.points == task.points
    assert imported.estimate == task.estimate
    assert imported.reviewed == task.reviewed


def test_default_values_integration():
    """Test that default values work correctly in real scenarios."""

    class DefaultedTask(Task):
        priority_score: float = 1.0
        risk_level: str = "low"
        auto_close: bool = False

    task1 = DefaultedTask(description="Task 1")

    assert task1.priority_score == 1.0
    assert task1.risk_level == "low"
    assert task1.auto_close is False

    task2 = DefaultedTask(description="Task 2", priority_score=2.5, risk_level="high")

    assert task2.priority_score == 2.5
    assert task2.risk_level == "high"


def test_inheritance_with_validators():
    """Test that validators work correctly with UDA inheritance."""

    class BaseTaskWithValidation(Task):
        estimate: TWDuration | None = None

        @field_validator("estimate")
        @classmethod
        def validate_estimate(cls, v: timedelta | None) -> timedelta | None:
            if v and v > timedelta(days=30):
                raise ValueError("Estimate too long")
            return v

    task = BaseTaskWithValidation(description="Test", estimate=timedelta(days=7))
    assert task.estimate == timedelta(days=7)

    with pytest.raises(Exception):  # ValidationError
        BaseTaskWithValidation(description="Test", estimate=timedelta(days=60))
