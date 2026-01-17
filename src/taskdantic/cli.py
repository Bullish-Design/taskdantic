# src/taskdantic/cli.py
from __future__ import annotations

from typing import Annotated

import typer

from taskdantic.uda_sync import sync_taskrc_udas


cli = typer.Typer(help="Taskdantic command line interface.")


@cli.command("sync")
def sync(
    taskrc_path: Annotated[str, typer.Option("--taskrc", exists=True, dir_okay=False)],
    tasks_root: Annotated[str | None, typer.Option("--tasks-root", file_okay=False)] = None,
) -> None:
    """Sync taskrc UDAs from Task models."""
    sync_taskrc_udas(taskrc_path=taskrc_path, tasks_root=tasks_root)
