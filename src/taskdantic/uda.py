# src/taskdantic/uda.py
from __future__ import annotations

from typing import Any


def uda(
    *,
    label: str | None = None,
    type: str | None = None,
    values: list[str] | None = None,
    urgency: dict[str, float] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """
    Build json_schema_extra metadata for Taskwarrior UDAs.

    This helper returns a dict suitable for `json_schema_extra`, with all
    Taskwarrior metadata nested under the "taskwarrior" key.
    """
    metadata: dict[str, Any] = {}

    if label is not None:
        metadata["label"] = label
    if type is not None:
        metadata["type"] = type
    if values is not None:
        metadata["values"] = values
    if urgency is not None:
        metadata["urgency"] = urgency

    metadata.update(extra)

    return {"taskwarrior": metadata}
