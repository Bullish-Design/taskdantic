from __future__ import annotations

from typing import Literal
from datetime import timedelta

from pydantic import Field

from taskdantic import Task, TWDuration


class FinanceTask(Task):
    cost_center: str | None = Field(
        default=None,
        json_schema_extra={"taskwarrior": {"label": "Cost Center"}},
    )

    budget: float | None = Field(
        default=None,
        json_schema_extra={"taskwarrior": {"label": "Budget USD"}},
    )

    # Another duration UDA to confirm multiple modules merge fine
    timebox: TWDuration | None = Field(
        default=None,
        json_schema_extra={"taskwarrior": {"label": "Timebox"}},
    )

    # Literal without explicit values: exporter should infer values automatically
    risk: Literal["low", "medium", "high"] | None = Field(
        default=None,
        json_schema_extra={"taskwarrior": {"label": "Risk"}},
    )
