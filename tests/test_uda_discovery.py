# tests/test_uda_discovery.py
from __future__ import annotations

from taskdantic import Task
from taskdantic.uda_discovery import discover_task_models


class DiscoveryBaseTask(Task):
    alpha: str | None = None


class DiscoveryChildTask(DiscoveryBaseTask):
    beta: int | None = None


def test_discover_task_models_finds_subclasses() -> None:
    models = discover_task_models(allowed_modules={__name__})

    assert DiscoveryBaseTask in models
    assert DiscoveryChildTask in models
    assert Task not in models
