# tests/test_cli.py
from __future__ import annotations

from typer.testing import CliRunner

from taskdantic.cli import cli


def test_cli_sync_writes_taskrc(tmp_path) -> None:
    taskrc_path = tmp_path / "taskrc"
    taskrc_path.write_text("", encoding="utf-8")

    tasks_root = tmp_path / "tasks"
    tasks_root.mkdir()
    (tasks_root / "my_tasks.py").write_text(
        "\n".join(
            [
                "from pydantic import Field",
                "from taskdantic import Task",
                "",
                "class MyTask(Task):",
                "    mood: str = Field(default='ok', json_schema_extra={'taskwarrior': {'label': 'Mood'}})",
                "",
            ]
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["sync", "--taskrc", str(taskrc_path), "--tasks-root", str(tasks_root)],
    )

    assert result.exit_code == 0
    updated = taskrc_path.read_text(encoding="utf-8")
    assert "uda.mood.type=string" in updated
    assert "uda.mood.label=Mood" in updated
