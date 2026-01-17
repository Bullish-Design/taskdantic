# examples/uda_usage.py
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pydantic>=2.0.0",
# ]
# ///
from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

root_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, root_path)

from pydantic import Field, field_validator

from taskdantic import Priority, Task, TWDatetime, TWDuration, UUIDList


class AgileTask(Task):
    """Task for agile development with sprint tracking."""

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
    """Task for bug tracking."""

    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    reported_by: str | None = None
    fixed_in: str | None = None


def basic_usage() -> None:
    """Demonstrate basic UDA usage with custom types."""
    print("=== Basic Usage ===\n")

    task = AgileTask(
        description="Implement OAuth2 authentication",
        project="backend",
        tags=["security", "api"],
        priority=Priority.HIGH,
        sprint="23",
        points=8,
        estimate="PT6H30M",  # ISO 8601 duration
        reviewed="20240120T143000Z",  # Taskwarrior timestamp
    )

    print(f"Task: {task.description}")
    print(f"Sprint: {task.sprint}")
    print(f"Points: {task.points}")
    print(f"Estimate: {task.estimate}")
    print(f"Reviewed: {task.reviewed}\n")


def export_import() -> None:
    """Demonstrate export/import with custom types."""
    print("=== Export/Import ===\n")

    task = AgileTask(
        description="Refactor payment module",
        sprint="Sprint 24",
        points=13,
        estimate=timedelta(hours=10),
    )

    exported = task.to_taskwarrior()
    print("Exported JSON:")
    print(json.dumps(exported, indent=2, default=str))

    imported = AgileTask.from_taskwarrior(exported)
    print(f"\nImported - Sprint: {imported.sprint}, Points: {imported.points}\n")


def multiple_task_types() -> None:
    """Demonstrate using different task types."""
    print("=== Multiple Task Types ===\n")

    feature = AgileTask(
        description="Add user profile",
        sprint="Sprint 25",
        points=5,
        estimate=timedelta(hours=4),
    )

    bug = BugTask(
        description="Fix login redirect",
        severity="high",
        reported_by="user@example.com",
    )

    print(f"Feature: {feature.description} ({feature.points} points, {feature.estimate})")
    print(f"Bug: {bug.description} (severity: {bug.severity})\n")


def type_safety_demo() -> None:
    """Demonstrate type safety with custom types."""
    print("=== Type Safety ===\n")

    task = AgileTask(
        description="Type safety demo",
        sprint="26",
        points=8,
    )

    # Custom types handle parsing automatically
    task.estimate = "PT2H30M"  # String parsed to timedelta
    print(f"Estimate from string: {task.estimate} (type: {type(task.estimate).__name__})")

    task.reviewed = "20240120T143000Z"  # String parsed to datetime
    print(f"Reviewed from string: {task.reviewed}\n")


def working_with_collections() -> None:
    """Demonstrate working with collections of tasks."""
    print("=== Collections ===\n")

    tasks = [
        AgileTask(description="Task A", sprint="Sprint 27", points=8),
        AgileTask(description="Task B", sprint="Sprint 27", points=5),
        AgileTask(description="Task C", sprint="Sprint 28", points=3),
        AgileTask(description="Task D", sprint="Sprint 28", points=13),
    ]

    by_sprint: dict[str, list[AgileTask]] = {}
    for task in tasks:
        if task.sprint not in by_sprint:
            by_sprint[task.sprint] = []
        by_sprint[task.sprint].append(task)

    for sprint, sprint_tasks in sorted(by_sprint.items()):
        total_points = sum(t.points for t in sprint_tasks)
        print(f"{sprint}: {len(sprint_tasks)} tasks, {total_points} points")

    print()


def main() -> None:
    print("=== Taskdantic UDA Demo ===\n")

    basic_usage()
    export_import()
    multiple_task_types()
    type_safety_demo()
    working_with_collections()

    print("=== Demo Complete ===")


if __name__ == "__main__":
    main()
