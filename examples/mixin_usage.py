# examples/mixin_usage.py
from __future__ import annotations

from taskdantic import AgileUDAMixin, BugTrackingUDAMixin, FinanceUDAMixin, Task


class OperationalTask(AgileUDAMixin, BugTrackingUDAMixin, FinanceUDAMixin, Task):
    """Task with multiple UDA mixins composed together."""

    owner: str | None = None


if __name__ == "__main__":
    task = OperationalTask(
        description="Investigate payment retry failures",
        sprint="Sprint 42",
        points=5,
        ticket="PAY-431",
        severity="high",
        cost_center="FIN-OPS",
        budget=1200.50,
        billable="no",
        owner="finops",
    )

    print(task.model_dump())
    print("UDAs:", task.get_udas())
