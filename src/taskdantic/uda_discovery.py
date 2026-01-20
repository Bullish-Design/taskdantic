from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from typing import Iterable

from taskdantic.models import Task


def _iter_all_subclasses(cls: type) -> Iterable[type]:
    seen: set[type] = set()
    stack = list(cls.__subclasses__())
    while stack:
        sub = stack.pop()
        if sub in seen:
            continue
        seen.add(sub)
        yield sub
        stack.extend(sub.__subclasses__())


def _import_module_from_path(path: Path) -> str | None:
    """
    Import a python file by absolute path as an anonymous module.
    """
    # stable-ish unique module name to avoid collisions
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:12]
    mod_name = f"taskdantic_autoload_{digest}"

    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return mod_name


def import_task_modules_from_dir(root_dir: str | Path) -> set[str]:
    """
    Recursively import all *.py files under root_dir.
    Returns the module names assigned to imported modules.
    """
    root = Path(root_dir).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise NotADirectoryError(f"TASKDANTIC_TASKS_ROOT is not a directory: {root}")

    imported: set[str] = set()

    for path in root.rglob("*.py"):
        parts = set(path.parts)
        if "__pycache__" in parts:
            continue

        mod_name = _import_module_from_path(path)
        if mod_name:
            imported.add(mod_name)

    return imported


def discover_task_models(allowed_modules: set[str] | None = None) -> list[type[Task]]:
    """
    Discover Task subclasses currently registered in this process.
    """
    models: list[type[Task]] = []
    for sub in _iter_all_subclasses(Task):
        if isinstance(sub, type) and (allowed_modules is None or sub.__module__ in allowed_modules):
            models.append(sub)  # type: ignore[assignment]
    return models
