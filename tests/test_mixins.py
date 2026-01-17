# tests/test_mixins.py
from __future__ import annotations

from taskdantic import AgileUDAMixin, BugTrackingUDAMixin, FinanceUDAMixin, Task
from taskdantic.uda_export import extract_uda_specs


class MixedTask(AgileUDAMixin, BugTrackingUDAMixin, FinanceUDAMixin, Task):
    """Task composed from multiple UDA mixins."""

    owner: str | None = None


def test_mixins_expose_udas_on_task():
    task = MixedTask(description="Mixins", owner="ops")

    uda_names = set(task.get_udas().keys())

    assert uda_names == {
        "external_id",
        "sprint",
        "points",
        "estimate",
        "ticket",
        "severity",
        "reported",
        "cost_center",
        "budget",
        "billable",
        "owner",
    }


def test_mixins_uda_specs_are_discovered():
    specs = {spec.name: spec for spec in extract_uda_specs(MixedTask)}

    assert set(specs.keys()) == {
        "external_id",
        "sprint",
        "points",
        "estimate",
        "ticket",
        "severity",
        "reported",
        "cost_center",
        "budget",
        "billable",
        "owner",
    }
    assert specs["severity"].values == ["low", "medium", "high", "critical"]
    assert specs["budget"].type == "numeric"
