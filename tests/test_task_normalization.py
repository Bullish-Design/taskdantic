# tests/test_task_normalization.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from taskdantic import Annotation, Task


class PromptTask(Task):
    beta: str | None = None
    alpha: str | None = None


def test_normalized_for_prompt_orders_udas_and_truncates_annotations() -> None:
    task = PromptTask(
        uuid=UUID("12345678-1234-5678-1234-567812345678"),
        description="Normalize me",
        annotations=[
            Annotation(
                entry=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                description="first",
            ),
            Annotation(
                entry=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
                description="second",
            ),
        ],
        alpha="A",
        beta="B",
    )

    normalized = task.normalized_for_prompt(max_annotations=1)

    keys = list(normalized.keys())

    assert keys.index("description") < keys.index("alpha")
    assert keys[-2:] == ["alpha", "beta"]
    assert len(normalized["annotations"]) == 1
    assert normalized["annotations"][0]["description"] == "first"
