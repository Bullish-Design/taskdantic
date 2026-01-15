# tests/fixtures/sample_data.py
from __future__ import annotations

from datetime import datetime, timedelta


class SampleData:
    """Predefined sample data sets for consistent testing."""

    PROJECTS = [
        "work",
        "personal",
        "home",
        "urgent",
        "test_project",
    ]

    TAGS = [
        "important",
        "urgent",
        "waiting",
        "someday",
        "test",
        "bug",
        "feature",
        "review",
    ]

    PRIORITIES = ["H", "M", "L"]

    DESCRIPTIONS = [
        "Review pull request",
        "Write documentation",
        "Fix bug in authentication",
        "Update dependencies",
        "Deploy to production",
        "Meeting with team",
        "Code review",
        "Research new framework",
        "Refactor database queries",
        "Write unit tests",
    ]

    @staticmethod
    def get_tasks_for_project(project: str, count: int = 5) -> list[dict]:
        """Generate tasks for specific project."""
        tasks = []
        for i in range(count):
            tasks.append({
                "description": f"{project.capitalize()} task {i + 1}",
                "project": project,
                "priority": SampleData.PRIORITIES[i % len(SampleData.PRIORITIES)],
            })
        return tasks

    @staticmethod
    def get_tasks_with_due_dates(count: int = 5) -> list[dict]:
        """Generate tasks with varying due dates."""
        tasks = []
        base_date = datetime.now()
        for i in range(count):
            due_date = base_date + timedelta(days=i + 1)
            tasks.append({
                "description": f"Task due in {i + 1} days",
                "due": due_date.strftime("%Y-%m-%dT%H:%M:%S"),
            })
        return tasks

    @staticmethod
    def get_tasks_with_tags(tag: str, count: int = 3) -> list[dict]:
        """Generate tasks with specific tag."""
        tasks = []
        for i in range(count):
            tasks.append({
                "description": f"Task with {tag} tag {i + 1}",
                "tags": [tag],
            })
        return tasks

    @staticmethod
    def get_mixed_priority_tasks() -> list[dict]:
        """Generate tasks with all priority levels."""
        return [
            {"description": "High priority task", "priority": "H"},
            {"description": "Medium priority task", "priority": "M"},
            {"description": "Low priority task", "priority": "L"},
            {"description": "No priority task"},
        ]

    @staticmethod
    def get_annotation_text() -> list[str]:
        """Common annotation strings for testing."""
        return [
            "This is important",
            "Remember to check dependencies",
            "Follow up with team",
            "Blocked by issue #123",
            "Special chars: !@#$%",
            "Unicode: 你好 🎉",
        ]

    @staticmethod
    def get_filter_strings() -> dict[str, str]:
        """Common filter strings for testing."""
        return {
            "pending": "status:pending",
            "completed": "status:completed",
            "high_priority": "priority:H",
            "work_project": "project:work",
            "urgent_tag": "+urgent",
            "complex_and": "project:work status:pending priority:H",
            "complex_or": "(status:pending or status:waiting)",
            "date_range": "due.after:today due.before:eom",
            "negative": "status:pending -urgent",
        }
