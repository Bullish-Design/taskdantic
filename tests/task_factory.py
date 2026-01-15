# tests/fixtures/task_factory.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


class TaskFactory:
    """Factory for creating test task data with various configurations."""

    @staticmethod
    def minimal() -> dict[str, Any]:
        """Minimal valid task data."""
        return {"description": "Test task"}

    @staticmethod
    def complete() -> dict[str, Any]:
        """Task with all standard fields populated."""
        return {
            "description": "Complete test task",
            "project": "test_project",
            "priority": "H",
            "tags": ["test", "important"],
            "due": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    @staticmethod
    def with_project(project: str = "work") -> dict[str, Any]:
        """Task with specific project."""
        return {
            "description": f"Task in {project}",
            "project": project,
        }

    @staticmethod
    def with_priority(priority: str = "H") -> dict[str, Any]:
        """Task with specific priority."""
        return {
            "description": f"Priority {priority} task",
            "priority": priority,
        }

    @staticmethod
    def with_tags(tags: list[str] | None = None) -> dict[str, Any]:
        """Task with specific tags."""
        if tags is None:
            tags = ["tag1", "tag2"]
        return {
            "description": "Task with tags",
            "tags": tags,
        }

    @staticmethod
    def with_due_date(days_from_now: int = 7) -> dict[str, Any]:
        """Task with due date N days from now."""
        due_date = datetime.now() + timedelta(days=days_from_now)
        return {
            "description": "Task with due date",
            "due": due_date.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    @staticmethod
    def with_udas(**udas: Any) -> dict[str, Any]:
        """Task with user-defined attributes."""
        task = TaskFactory.minimal()
        task.update(udas)
        return task

    @staticmethod
    def batch(count: int = 10, vary: bool = True) -> list[dict[str, Any]]:
        """Generate batch of task data.

        Args:
            count: Number of tasks to generate
            vary: If True, vary fields across tasks; if False, all minimal

        Returns:
            List of task data dictionaries
        """
        if not vary:
            return [TaskFactory.minimal() for _ in range(count)]

        tasks = []
        projects = ["work", "personal", "home", None]
        priorities = ["H", "M", "L", None]
        tag_sets = [["urgent"], ["important"], ["urgent", "important"], []]

        for i in range(count):
            task = {
                "description": f"Test task {i + 1}",
                "project": projects[i % len(projects)],
                "priority": priorities[i % len(priorities)],
                "tags": tag_sets[i % len(tag_sets)],
            }
            # Remove None values
            task = {k: v for k, v in task.items() if v is not None}
            tasks.append(task)

        return tasks

    @staticmethod
    def with_special_chars() -> dict[str, Any]:
        """Task with special characters in various fields."""
        return {
            "description": "Task with special chars: !@#$%^&*()_+-=[]{}|;:',.<>?/~`",
            "project": "test-project_2024",
            "tags": ["tag-with-dash", "tag_with_underscore"],
        }

    @staticmethod
    def with_unicode() -> dict[str, Any]:
        """Task with unicode characters."""
        return {
            "description": "Unicode task: 你好世界 🌍 café naïve",
            "project": "проект",
            "tags": ["日本語", "emoji🎉"],
        }

    @staticmethod
    def long_description(length: int = 1000) -> dict[str, Any]:
        """Task with very long description."""
        return {
            "description": "A" * length,
        }
