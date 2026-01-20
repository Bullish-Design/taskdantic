# src/taskdantic/uda_sync.py
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path
from taskdantic.uda_discovery import discover_task_models, import_task_modules_from_dir
from taskdantic.uda_export import extract_uda_specs, merge_uda_specs, render_taskrc_udas
from taskdantic.uda_taskrc import (
    parse_existing_uda_names as _parse_existing_uda_names,
    upsert_uda_block as _upsert_uda_block,
)

def parse_existing_uda_names(taskrc_text: str) -> set[str]:
    warnings.warn(
        "parse_existing_uda_names is deprecated; import from taskdantic.uda_taskrc instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _parse_existing_uda_names(taskrc_text)


def upsert_uda_block(taskrc_text: str, block_body: str) -> str:
    warnings.warn(
        "upsert_uda_block is deprecated; import from taskdantic.uda_taskrc instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _upsert_uda_block(taskrc_text, block_body)


def sync_taskrc_udas(taskrc_path: str, tasks_root: str | None = None, *, strict: bool = False) -> None:
    """
    Generate UDAs from all discovered Task subclasses and upsert them into taskrc.

    If tasks_root is provided, import every matching python file under that directory first.
    """
    path = Path(taskrc_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"taskrc file not found: {path}")

    if tasks_root:
        imported_modules = import_task_modules_from_dir(tasks_root)
    else:
        imported_modules = None

    original = path.read_text(encoding="utf-8")
    existing = _parse_existing_uda_names(original)

    models = discover_task_models(imported_modules)
    spec_map = merge_uda_specs(extract_uda_specs(m) for m in models)
    generated_names = set(spec_map.keys())

    missing_in_code = existing - generated_names
    if missing_in_code:
        msg = f"[taskdantic] taskrc defines UDAs not generated from code: {sorted(missing_in_code)}"
        if strict:
            raise ValueError(msg)
        print(msg, file=sys.stderr)

    block_body = render_taskrc_udas(spec_map.values())
    updated = _upsert_uda_block(original, block_body)

    if updated != original:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(updated, encoding="utf-8")
        tmp.replace(path)


def auto_sync_taskrc_from_env() -> None:
    """
    Startup hook:
      - TASKRC_PATH must be set and exist
      - TASKDANTIC_TASKS_ROOT (optional): directory root to scan/import recursively
      - TASKDANTIC_STRICT_UDAS (optional): "1"/"true" to fail on unmanaged UDAs
    """
    print(f"\n[taskdantic] Auto-syncing UDAs into taskrc from environment...")
    from dotenv import load_dotenv

    load_dotenv()
    taskrc_path = os.getenv("TASKRC_PATH")
    print(f"[taskdantic] Using TASKRC_PATH={taskrc_path}")
    if not taskrc_path:
        return

    tasks_root = os.getenv("TASKDANTIC_TASKS_ROOT")
    print(f"[taskdantic] Using TASKDANTIC_TASKS_ROOT={tasks_root}")
    strict_env = os.getenv("TASKDANTIC_STRICT_UDAS", "").strip().lower()
    strict = strict_env in {"1", "true", "yes", "on"}
    print(f"[taskdantic] Using TASKDANTIC_STRICT_UDAS={strict}")

    sync_taskrc_udas(taskrc_path=taskrc_path, tasks_root=tasks_root, strict=strict)
    print(f"[taskdantic] UDA sync complete.\n")


if __name__ == "__main__":
    auto_sync_taskrc_from_env()
