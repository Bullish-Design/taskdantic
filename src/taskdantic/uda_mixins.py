# src/taskdantic/uda_mixins.py
from __future__ import annotations

from typing import Literal

from pydantic import Field

from taskdantic.task_types import TWDatetime, TWDuration
from taskdantic.uda import uda


class UDAMixin:
    """Base mixin for shared Taskwarrior UDAs."""

    external_id: str | None = Field(
        default=None,
        json_schema_extra=uda(label="External ID"),
    )


class AgileUDAMixin(UDAMixin):
    """UDAs for Agile tracking."""

    sprint: str | None = Field(
        default=None,
        json_schema_extra=uda(label="Sprint"),
    )
    points: int | None = Field(
        default=None,
        json_schema_extra=uda(label="Story Points", type="numeric"),
    )
    estimate: TWDuration | None = Field(
        default=None,
        json_schema_extra=uda(label="Estimate", type="duration"),
    )


class BugTrackingUDAMixin(UDAMixin):
    """UDAs for bug tracking."""

    ticket: str | None = Field(
        default=None,
        json_schema_extra=uda(label="Ticket"),
    )
    severity: Literal["low", "medium", "high", "critical"] | None = Field(
        default=None,
        json_schema_extra=uda(label="Severity", values=["low", "medium", "high", "critical"]),
    )
    reported: TWDatetime | None = Field(
        default=None,
        json_schema_extra=uda(label="Reported", type="date"),
    )


class FinanceUDAMixin(UDAMixin):
    """UDAs for finance tracking."""

    cost_center: str | None = Field(
        default=None,
        json_schema_extra=uda(label="Cost Center"),
    )
    budget: float | None = Field(
        default=None,
        json_schema_extra=uda(label="Budget", type="numeric"),
    )
    billable: Literal["yes", "no"] | None = Field(
        default=None,
        json_schema_extra=uda(label="Billable", values=["yes", "no"]),
    )
