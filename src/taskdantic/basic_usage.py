#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "taskdantic",
# ]
# ///

# examples/basic_usage.py

"""Basic usage example for taskdantic library."""

from __future__ import annotations

from taskdantic import Priority, TaskStatus, TaskWarrior


def main() -> None:
    """Demonstrate basic taskdantic operations."""
    tw = TaskWarrior()

    # Verify installation
    if not tw.verify_installation():
        print("Taskwarrior not found. Please install it first.")
        return

    print(f"Taskwarrior version: {tw.get_version()}")

    # Add a task
    print("\n1. Adding a task...")
    task = tw.add(
        "Complete taskdantic library",
        project="development",
        tags=["python", "taskwarrior"],
        priority=Priority.HIGH,
    )
    print(f"Created task: {task.uuid}")
    print(f"Description: {task.description}")
    print(f"Project: {task.project}")
    print(f"Tags: {', '.join(task.tags)}")

    # Get the task
    print("\n2. Getting the task...")
    fetched = tw.get(uuid=task.uuid)
    print(f"Fetched: {fetched.description}")

    # Update the task
    print("\n3. Updating the task...")
    fetched.priority = Priority.MEDIUM
    fetched.tags.append("library")
    updated = tw.update(fetched)
    print(f"Updated priority: {updated.priority}")
    print(f"Updated tags: {', '.join(updated.tags)}")

    # Start the task
    print("\n4. Starting the task...")
    started = tw.start(uuid=task.uuid)
    print(f"Started: {started.start}")

    # Add annotation
    print("\n5. Adding annotation...")
    annotated = tw.annotate(task.uuid, "Making good progress")
    print(f"Annotations: {len(annotated.annotations)}")

    # Load all pending tasks
    print("\n6. Loading pending tasks...")
    pending = tw.load_tasks(status=TaskStatus.PENDING)
    print(f"Total pending tasks: {len(pending)}")

    # Filter tasks
    print("\n7. Filtering tasks by project...")
    project_tasks = tw.filter_tasks("project:development")
    print(f"Tasks in 'development': {len(project_tasks)}")
    for t in project_tasks[:5]:
        print(f"  - {t.description}")

    # Complete the task
    print("\n8. Completing the task...")
    completed = tw.complete(uuid=task.uuid)
    print(f"Completed: {completed.status}")

    print("\nDone!")


if __name__ == "__main__":
    main()
