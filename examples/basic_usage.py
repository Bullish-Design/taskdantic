# examples/basic_usage.py
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pydantic>=2.0.0",
# ]
# ///
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta

import sys
from pathlib import Path

root_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, root_path)

from pydantic import field_validator

from taskdantic import Priority, Status, Task, TWDuration


class AgileTask(Task):
    """Task with Agile UDAs for sprint tracking."""

    sprint: str | None = None
    points: int = 0
    estimate: TWDuration | None = None

    @field_validator("sprint")
    @classmethod
    def validate_sprint(cls, v: str | None) -> str | None:
        if v and not v.startswith("Sprint "):
            return f"Sprint {v}"
        return v


def create_new_task() -> AgileTask:
    """Create a new task with UDAs programmatically."""
    task = AgileTask(
        description="Write documentation for Taskdantic",
        project="taskdantic",
        tags=["coding", "docs"],
        priority=Priority.HIGH,
        due=datetime.now() + timedelta(days=7),
        sprint="23",
        points=5,
        estimate=timedelta(hours=4),
    )
    return task


def export_to_taskwarrior(task: AgileTask) -> None:
    """Export task to JSON format for Taskwarrior import."""
    task_json = json.dumps(task.export_dict())
    print("Export for Taskwarrior:")
    print(task_json)
    print("\nTo import: echo '<json>' | task import -")


def import_from_taskwarrior() -> None:
    """Import tasks from Taskwarrior export."""
    try:
        result = subprocess.run(
            ["task", "export"],
            capture_output=True,
            text=True,
            check=True,
        )
        tasks_data = json.loads(result.stdout)

        print(f"\nFound {len(tasks_data)} tasks in Taskwarrior")

        for task_data in tasks_data:
            task = AgileTask.from_taskwarrior(task_data)
            print(f"- {task.description} [{task.status.value}]")

    except subprocess.CalledProcessError:
        print("Taskwarrior not installed or no tasks found")
    except json.JSONDecodeError:
        print("Failed to parse Taskwarrior export")


def main() -> None:
    print("=== Taskdantic Demo ===\n")

    task = create_new_task()
    print(f"Created task: {task.description}")
    print(f"UUID: {task.uuid}")
    print(f"Status: {task.status.value}")
    print(f"Priority: {task.priority.value if task.priority else 'None'}")
    print(f"Sprint: {task.sprint}")
    print(f"Points: {task.points}")
    print(f"Estimate: {task.estimate}")

    export_to_taskwarrior(task)
    import_from_taskwarrior()


if __name__ == "__main__":
    main()
