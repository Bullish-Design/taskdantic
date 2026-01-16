# tests/conftest.py
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from taskdantic import TaskWarrior


@pytest.fixture
def temp_taskwarrior() -> Generator[TaskWarrior, None, None]:
    """Provide isolated TaskWarrior instance with temporary database.

    Creates a temporary directory structure:
    - {temp_dir}/.task/ for task data
    - {temp_dir}/.taskrc for configuration

    Yields:
        TaskWarrior instance configured to use temp database

    Cleanup:
        Removes temporary directory after test
    """
    temp_dir = tempfile.mkdtemp(prefix="taskdantic_test_")
    task_dir = Path(temp_dir) / ".task"
    task_dir.mkdir(parents=True)

    taskrc_path = Path(temp_dir) / ".taskrc"
    taskrc_content = f"""
data.location={task_dir}
confirmation=off
json.array=on
hooks=off
context=none
"""
    taskrc_path.write_text(taskrc_content.strip())

    tw = TaskWarrior(
        config_filename=str(taskrc_path),
        config_overrides={
            "confirmation": "off",
            "json.array": "on",
        },
    )

    try:
        yield tw
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_taskwarrior_with_udas() -> Generator[TaskWarrior, None, None]:
    """Provide TaskWarrior instance with UDA definitions for testing.

    Includes common UDAs:
    - estimate (numeric): Time estimate in hours
    - complexity (string): Task complexity level
    - reviewed (date): Review date

    Yields:
        TaskWarrior instance with UDAs configured
    """
    temp_dir = tempfile.mkdtemp(prefix="taskdantic_uda_test_")
    task_dir = Path(temp_dir) / ".task"
    task_dir.mkdir(parents=True)

    taskrc_path = Path(temp_dir) / ".taskrc"
    taskrc_content = f"""
data.location={task_dir}
confirmation=off
json.array=on
hooks=off
context=none

uda.estimate.type=numeric
uda.estimate.label=Estimate
uda.estimate.values=

uda.complexity.type=string
uda.complexity.label=Complexity
uda.complexity.values=low,medium,high

uda.reviewed.type=date
uda.reviewed.label=Reviewed
"""
    taskrc_path.write_text(taskrc_content.strip())

    tw = TaskWarrior(config_filename=str(taskrc_path))

    try:
        yield tw
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide temporary directory for test files.

    Yields:
        Path to temporary directory

    Cleanup:
        Removes directory after test
    """
    temp_path = Path(tempfile.mkdtemp(prefix="taskdantic_files_"))
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)
