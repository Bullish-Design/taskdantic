# src/taskdantic/warrior.py

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from taskdantic.config import TaskRcParser
from taskdantic.exceptions import (
    TaskNotFoundError,
    TaskWarriorCommandError,
    TaskWarriorNotInstalledError,
)
from taskdantic.models import Task, TaskConfig
from taskdantic.types import Priority, TaskFilter, TaskStatus
from taskdantic.utils import format_filter, parse_task_export, task_to_json


class TaskWarrior:
    """Interface to Taskwarrior via subprocess calls."""

    def __init__(
        self,
        config_filename: Optional[str | Path] = None,
        config_overrides: Optional[dict[str, Any]] = None,
        task_command: str = "task",
    ):
        """Initialize TaskWarrior interface.

        Args:
            config_filename: Path to .taskrc file (None for default)
            config_overrides: Dict of config values to override
            task_command: Path to task executable
        """
        self.config_filename = Path(config_filename) if config_filename else None
        self.config_overrides = config_overrides or {}
        self.task_command = task_command
        self._config: Optional[TaskConfig] = None
        self._version: Optional[str] = None

    def load_config(self) -> TaskConfig:
        """Load and parse taskrc configuration."""
        if self._config is not None:
            return self._config

        if self.config_filename:
            parser = TaskRcParser(self.config_filename)
            self._config = parser.parse()
        else:
            # Use default taskrc location
            default_rc = Path.home() / ".taskrc"
            if default_rc.exists():
                parser = TaskRcParser(default_rc)
                self._config = parser.parse()
            else:
                self._config = TaskConfig()

        return self._config

    def get_version(self) -> str:
        """Get Taskwarrior version."""
        if self._version is not None:
            return self._version

        try:
            result = subprocess.run(
                [self.task_command, "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            self._version = result.stdout.strip()
            return self._version
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise TaskWarriorNotInstalledError(
                f"Failed to get task version: {e}"
            ) from e

    def verify_installation(self) -> bool:
        """Check if Taskwarrior is installed and accessible."""
        return shutil.which(self.task_command) is not None

    def add(
        self,
        description: str,
        *,
        project: Optional[str] = None,
        tags: Optional[list[str]] = None,
        priority: Optional[Priority] = None,
        **kwargs: Any,
    ) -> Task:
        """Add a new task.

        Args:
            description: Task description
            project: Project name
            tags: List of tags
            priority: Task priority
            **kwargs: Additional task attributes (including UDAs)

        Returns:
            Created Task object
        """
        # Build task data
        task_data: dict[str, Any] = {
            "description": description,
            "status": TaskStatus.PENDING.value,
        }

        if project:
            task_data["project"] = project
        if tags:
            task_data["tags"] = tags
        if priority:
            task_data["priority"] = priority.value

        # Add any additional fields
        task_data.update(kwargs)

        # Create task via import
        task = Task.model_validate(task_data)
        json_data = task_to_json(task)

        # Use 'task import' to add the task
        try:
            stdout, _ = self._execute("import", "-", stdin=json_data)
            # Parse the result to get the created task with UUID
            tasks = parse_task_export(stdout)
            if tasks:
                return tasks[0]
            raise TaskWarriorCommandError("No task returned from import")
        except Exception as e:
            raise TaskWarriorCommandError(f"Failed to add task: {e}") from e

    def get(
        self,
        *,
        uuid: Optional[UUID | str] = None,
        id: Optional[int] = None,
    ) -> Task:
        """Get a task by UUID or ID.

        Args:
            uuid: Task UUID
            id: Task ID (runtime only)

        Returns:
            Task object

        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        if uuid is None and id is None:
            raise ValueError("Must provide either uuid or id")

        filter_str = f"uuid:{uuid}" if uuid else str(id)
        tasks = self.filter_tasks(filter_str)

        if not tasks:
            identifier = str(uuid) if uuid else str(id)
            raise TaskNotFoundError(f"Task not found: {identifier}")

        return tasks[0]

    def update(self, task: Task) -> Task:
        """Update an existing task.

        Args:
            task: Task object with updated fields

        Returns:
            Updated Task object
        """
        if task.uuid is None:
            raise ValueError("Task must have UUID to update")

        # Export current task to get all fields
        try:
            current = self.get(uuid=task.uuid)
        except TaskNotFoundError as e:
            raise TaskNotFoundError(f"Cannot update non-existent task: {task.uuid}") from e

        # Build modification arguments
        args = ["modify"]

        # Add UUID filter
        args.append(f"uuid:{task.uuid}")

        # Build modification commands
        if task.description != current.description:
            args.append(task.description)

        if task.project != current.project:
            if task.project:
                args.append(f"project:{task.project}")
            else:
                args.append("project:")

        if task.priority != current.priority:
            if task.priority:
                args.append(f"priority:{task.priority.value}")
            else:
                args.append("priority:")

        # Handle tags
        if set(task.tags) != set(current.tags):
            for tag in current.tags:
                if tag not in task.tags:
                    args.append(f"-{tag}")
            for tag in task.tags:
                if tag not in current.tags:
                    args.append(f"+{tag}")

        # Handle due date
        if task.due != current.due:
            if task.due:
                due_str = task.due.strftime("%Y-%m-%dT%H:%M:%S")
                args.append(f"due:{due_str}")
            else:
                args.append("due:")

        # Execute modification if there are changes
        if len(args) > 2:
            self._execute(*args)

        # Fetch updated task
        return self.get(uuid=task.uuid)

    def delete(
        self,
        *,
        uuid: Optional[UUID | str] = None,
        id: Optional[int] = None,
    ) -> Task:
        """Delete a task.

        Args:
            uuid: Task UUID
            id: Task ID

        Returns:
            Deleted Task object
        """
        task = self.get(uuid=uuid, id=id)
        filter_str = f"uuid:{task.uuid}"
        self._execute(filter_str, "delete", "rc.confirmation=off")
        return task

    def complete(
        self,
        *,
        uuid: Optional[UUID | str] = None,
        id: Optional[int] = None,
    ) -> Task:
        """Mark a task as completed.

        Args:
            uuid: Task UUID
            id: Task ID

        Returns:
            Completed Task object
        """
        task = self.get(uuid=uuid, id=id)
        filter_str = f"uuid:{task.uuid}"
        self._execute(filter_str, "done")
        return self.get(uuid=task.uuid)

    def start(
        self,
        *,
        uuid: Optional[UUID | str] = None,
        id: Optional[int] = None,
    ) -> Task:
        """Start a task.

        Args:
            uuid: Task UUID
            id: Task ID

        Returns:
            Started Task object
        """
        task = self.get(uuid=uuid, id=id)
        filter_str = f"uuid:{task.uuid}"
        self._execute(filter_str, "start")
        return self.get(uuid=task.uuid)

    def stop(
        self,
        *,
        uuid: Optional[UUID | str] = None,
        id: Optional[int] = None,
    ) -> Task:
        """Stop a task.

        Args:
            uuid: Task UUID
            id: Task ID

        Returns:
            Stopped Task object
        """
        task = self.get(uuid=uuid, id=id)
        filter_str = f"uuid:{task.uuid}"
        self._execute(filter_str, "stop")
        return self.get(uuid=task.uuid)

    def load_tasks(
        self,
        status: Optional[TaskStatus | list[TaskStatus]] = None,
    ) -> list[Task]:
        """Load tasks, optionally filtered by status.

        Args:
            status: Single status or list of statuses to filter by

        Returns:
            List of Task objects
        """
        if status is None:
            filter_str = ""
        elif isinstance(status, TaskStatus):
            filter_str = f"status:{status.value}"
        else:
            statuses = " or ".join(f"status:{s.value}" for s in status)
            filter_str = f"( {statuses} )"

        return self.filter_tasks(filter_str)

    def filter_tasks(self, filter: TaskFilter) -> list[Task]:
        """Filter tasks using Taskwarrior filter syntax.

        Args:
            filter: Filter string or dict

        Returns:
            List of matching Task objects
        """
        filter_str = format_filter(filter)
        args = []
        if filter_str:
            args.append(filter_str)
        args.append("export")

        stdout, _ = self._execute(*args)
        return parse_task_export(stdout)

    def annotate(
        self,
        task: Task | UUID | str,
        annotation: str,
    ) -> Task:
        """Add annotation to a task.

        Args:
            task: Task object or UUID
            annotation: Annotation text

        Returns:
            Updated Task object
        """
        if isinstance(task, Task):
            if task.uuid is None:
                raise ValueError("Task must have UUID")
            uuid = task.uuid
        else:
            uuid = task

        filter_str = f"uuid:{uuid}"
        self._execute(filter_str, "annotate", annotation)
        return self.get(uuid=uuid)

    def denotate(
        self,
        task: Task | UUID | str,
        annotation: str,
    ) -> Task:
        """Remove annotation from a task.

        Args:
            task: Task object or UUID
            annotation: Annotation text to remove

        Returns:
            Updated Task object
        """
        if isinstance(task, Task):
            if task.uuid is None:
                raise ValueError("Task must have UUID")
            uuid = task.uuid
        else:
            uuid = task

        filter_str = f"uuid:{uuid}"
        self._execute(filter_str, "denotate", annotation)
        return self.get(uuid=uuid)

    def _execute(
        self,
        *args: str,
        stdin: Optional[str] = None,
    ) -> tuple[str, str]:
        """Execute a task command and return stdout, stderr.

        Args:
            *args: Command arguments
            stdin: Optional stdin input

        Returns:
            Tuple of (stdout, stderr)

        Raises:
            TaskWarriorCommandError: If command fails
        """
        cmd = [self.task_command]

        # Add config overrides
        for key, value in self.config_overrides.items():
            cmd.append(f"rc.{key}={value}")

        # Add config file if specified
        if self.config_filename:
            cmd.append(f"rc:{self.config_filename}")

        cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                input=stdin,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            raise TaskWarriorCommandError(
                f"Command failed: {' '.join(cmd)}\n"
                f"stdout: {e.stdout}\n"
                f"stderr: {e.stderr}"
            ) from e
        except FileNotFoundError as e:
            raise TaskWarriorNotInstalledError(
                f"Task command not found: {self.task_command}"
            ) from e

    def _build_override_args(self) -> list[str]:
        """Build list of config override arguments."""
        args = []
        for key, value in self.config_overrides.items():
            args.append(f"rc.{key}={value}")
        return args
