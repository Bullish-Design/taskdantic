# tests/test_uda_registry.py
from __future__ import annotations

from pydantic import Field

from taskdantic import Task, uda
from taskdantic.uda_registry import UDARegistry


class RegistryTaskAlpha(Task):
    alpha: str | None = Field(
        default=None,
        json_schema_extra=uda(
            label="Alpha Label",
            values=["one", "two"],
            urgency={"low": 1.0, "high": 2.0},
        ),
    )


class RegistryTaskBeta(Task):
    beta: int | None = Field(
        default=None,
        json_schema_extra=uda(label="Beta Label", type="numeric"),
    )


def test_uda_registry_lists_sorted_specs() -> None:
    registry = UDARegistry.from_task_models([RegistryTaskBeta, RegistryTaskAlpha])

    names = [spec.name for spec in registry.list()]

    assert names == ["alpha", "beta"]


def test_uda_registry_prompt_context_formatting() -> None:
    registry = UDARegistry.from_task_models([RegistryTaskAlpha, RegistryTaskBeta])

    context = registry.as_prompt_context()

    assert context.splitlines() == [
        "Taskwarrior UDA definitions:",
        "- alpha (string) label=Alpha Label values=one, two urgency=low:1.0, high:2.0",
        "- beta (numeric) label=Beta Label",
    ]
