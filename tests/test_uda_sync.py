# tests/test_uda_sync.py
from __future__ import annotations

from pathlib import Path

from taskdantic.uda_sync import sync_taskrc_udas


def test_sync_taskrc_udas_imports_task_module(tmp_path: Path) -> None:
    tasks_file = tmp_path / "tasks.py"
    tasks_file.write_text(
        "\n".join(
            [
                "from taskdantic import Task",
                "",
                "",
                "class SprintTask(Task):",
                "    sprint: str",
                "",
            ]
        ),
        encoding="utf-8",
    )

    taskrc_path = tmp_path / "taskrc"
    taskrc_path.write_text("# taskrc\n", encoding="utf-8")

    sync_taskrc_udas(str(taskrc_path), tasks_root=str(tmp_path))

    updated = taskrc_path.read_text(encoding="utf-8")
    assert "uda.sprint.type=string" in updated
