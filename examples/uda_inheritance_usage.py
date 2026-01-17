# examples/uda_inheritance_usage.py
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pydantic>=2.0.0",
# ]
# ///
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

root_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, root_path)

from pydantic import Field, field_validator

from taskdantic import Priority, Status, Task, TWDatetime, TWDuration


# Define your custom Task types with UDAs as Pydantic fields
class AgileTask(Task):
    """Task for agile development with sprint tracking."""

    sprint: str | None = None
    points: int = 0
    estimate: TWDuration | None = None
    reviewed: TWDatetime | None = None

    @field_validator("sprint")
    @classmethod
    def validate_sprint(cls, v: str | None) -> str | None:
        """Auto-prefix sprint names."""
        if v and not v.startswith("Sprint "):
            return f"Sprint {v}"
        return v


class BugTask(Task):
    """Task for bug tracking."""

    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    reported_by: str | None = None
    fixed_in: str | None = None


class DevOpsTask(Task):
    """Task for deployment tracking."""

    environment: str | None = Field(default=None, pattern="^(dev|staging|prod)$")
    deployment_time: TWDatetime | None = None
    rollback_safe: bool = True


def basic_usage() -> None:
    """Demonstrate basic UDA usage through inheritance."""
    print("=== Basic Usage ===\n")

    task = AgileTask(
        description="Implement OAuth2 authentication",
        project="backend",
        tags=["security", "api"],
        priority=Priority.HIGH,
        sprint="23",  # Validator adds "Sprint " prefix
        points=8,
        estimate=timedelta(hours=6, minutes=30),
    )

    print(f"Task: {task.description}")
    print(f"Sprint: {task.sprint}")
    print(f"Points: {task.points}")
    print(f"Estimate: {task.estimate}")
    print(f"Priority: {task.priority.value}\n")


def export_import() -> None:
    """Demonstrate export/import with UDAs."""
    print("=== Export/Import ===\n")

    task = AgileTask(
        description="Refactor payment module",
        sprint="Sprint 24",
        points=13,
        estimate=timedelta(hours=10),
    )

    # Export to Taskwarrior format
    exported = task.export_dict()
    print("Exported JSON:")
    print(json.dumps(exported, indent=2, default=str))

    # Import back
    imported = AgileTask.from_taskwarrior(exported)
    print(f"\nImported - Sprint: {imported.sprint}, Points: {imported.points}\n")


def multiple_task_types() -> None:
    """Demonstrate using different task types."""
    print("=== Multiple Task Types ===\n")

    feature = AgileTask(
        description="Add user profile",
        sprint="Sprint 25",
        points=5,
    )

    bug = BugTask(
        description="Fix login redirect",
        severity="high",
        reported_by="user@example.com",
    )

    deploy = DevOpsTask(
        description="Deploy to production",
        environment="prod",
        rollback_safe=False,
    )

    print(f"Feature: {feature.description} ({feature.points} points)")
    print(f"Bug: {bug.description} (severity: {bug.severity})")
    print(f"Deploy: {deploy.description} (env: {deploy.environment})\n")


def type_safety_demo() -> None:
    """Demonstrate type safety and validation."""
    print("=== Type Safety ===\n")

    task = AgileTask(
        description="Type safety demo",
        sprint="26",  # Validator auto-prefixes
        points="8",  # Coerced to int
    )

    print(f"Sprint (auto-prefixed): {task.sprint}")
    print(f"Points (coerced from string): {task.points} (type: {type(task.points).__name__})")

    # Datetime handling
    task.reviewed = "20240120T143000Z"
    print(f"Reviewed (parsed timestamp): {task.reviewed}")

    # Duration handling
    task.estimate = "PT2H30M"
    print(f"Estimate (parsed ISO 8601): {task.estimate}\n")


def working_with_collections() -> None:
    """Demonstrate working with collections of tasks."""
    print("=== Collections ===\n")

    tasks = [
        AgileTask(description="Task A", sprint="Sprint 27", points=8),
        AgileTask(description="Task B", sprint="Sprint 27", points=5),
        AgileTask(description="Task C", sprint="Sprint 28", points=3),
        AgileTask(description="Task D", sprint="Sprint 28", points=13),
    ]

    # Group by sprint
    by_sprint: dict[str, list[AgileTask]] = {}
    for task in tasks:
        if task.sprint not in by_sprint:
            by_sprint[task.sprint] = []
        by_sprint[task.sprint].append(task)

    # Calculate totals
    for sprint, sprint_tasks in sorted(by_sprint.items()):
        total_points = sum(t.points for t in sprint_tasks)
        print(f"{sprint}: {len(sprint_tasks)} tasks, {total_points} points")

    print()


def taskwarrior_compatibility() -> None:
    """Demonstrate Taskwarrior compatibility."""
    print("=== Taskwarrior Compatibility ===\n")

    # Simulate data from 'task export'
    tw_data = {
        "id": 42,
        "uuid": "12345678-1234-5678-1234-567812345678",
        "description": "Imported from Taskwarrior",
        "status": "pending",
        "entry": "20240115T143022Z",
        "modified": "20240116T100000Z",
        "project": "backend",
        "tags": ["feature"],
        "urgency": 10.5,
        "sprint": "Sprint 28",
        "points": 5,
        "estimate": "PT4H",
    }

    # Import seamlessly
    task = AgileTask.from_taskwarrior(tw_data)

    print(f"Imported: {task.description}")
    print(f"Sprint: {task.sprint}")
    print(f"Points: {task.points}")
    print(f"Estimate: {task.estimate}")
    print(f"Computed fields ignored: id={hasattr(task, 'id')}, urgency={hasattr(task, 'urgency')}\n")


def lifecycle_tracking() -> None:
    """Demonstrate task lifecycle with UDAs."""
    print("=== Lifecycle Tracking ===\n")

    task = AgileTask(
        description="Implement feature",
        sprint="Sprint 29",
        points=8,
        estimate=timedelta(hours=6),
    )

    print(f"Created: {task.status.value}")

    # Start work
    task.status = Status.PENDING
    task.start = datetime.now()
    print(f"Started: {task.status.value}")

    # Review
    task.reviewed = datetime.now()
    print(f"Reviewed: {task.reviewed is not None}")

    # Complete
    task.status = Status.COMPLETED
    task.end = datetime.now()
    print(f"Completed: {task.status.value}\n")


def custom_inheritance() -> None:
    """Demonstrate custom inheritance patterns."""
    print("=== Custom Inheritance ===\n")

    class TrackedTask(Task):
        """Base task with time tracking."""

        time_spent: TWDuration | None = None

    class TrackedAgileTask(TrackedTask):
        """Agile task with time tracking."""

        sprint: str | None = None
        points: int = 0

    task = TrackedAgileTask(
        description="Feature with tracking",
        sprint="Sprint 30",
        points=5,
        time_spent=timedelta(hours=4, minutes=30),
    )

    print(f"Task: {task.description}")
    print(f"Sprint: {task.sprint}")
    print(f"Points: {task.points}")
    print(f"Time Spent: {task.time_spent}\n")


def main() -> None:
    print("=== Taskdantic UDA Inheritance Demo ===\n")

    basic_usage()
    export_import()
    multiple_task_types()
    type_safety_demo()
    working_with_collections()
    taskwarrior_compatibility()
    lifecycle_tracking()
    custom_inheritance()

    print("=== Demo Complete ===")


if __name__ == "__main__":
    main()
