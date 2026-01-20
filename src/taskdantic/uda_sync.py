# src/taskdantic/uda_sync.py
from __future__ import annotations

import os
import sys
from pathlib import Path
from taskdantic.uda_discovery import discover_task_models, import_task_modules_from_dir
from taskdantic.uda_export import extract_uda_specs, merge_uda_specs, render_taskrc_udas

BEGIN_MARKER = "# BEGIN TASKDANTIC UDAS"
END_MARKER = "# END TASKDANTIC UDAS"


def parse_existing_uda_names(taskrc_text: str) -> set[str]:
    names: set[str] = set()
    for raw in taskrc_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("uda.") and ".type=" in line:
            rest = line[len("uda.") :]
            name = rest.split(".type=", 1)[0].strip()
            if name:
                names.add(name)
    return names


def upsert_uda_block(taskrc_text: str, block_body: str) -> str:
    managed = (
        f"{BEGIN_MARKER}\n# Generated from Pydantic Task models. Do not edit by hand.\n\n{block_body}\n{END_MARKER}\n"
    )

    start = taskrc_text.find(BEGIN_MARKER)
    end = taskrc_text.find(END_MARKER)
    if start != -1 and end != -1 and start < end:
        pre = taskrc_text[:start].rstrip() + "\n\n"
        post = taskrc_text[end + len(END_MARKER) :].lstrip()
        return pre + managed + "\n" + post

    sep = "\n\n" if not taskrc_text.endswith("\n") else "\n"
    return taskrc_text + sep + managed


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
    existing = parse_existing_uda_names(original)

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
    updated = upsert_uda_block(original, block_body)

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
