# tests/test_uda.py
from __future__ import annotations

from pydantic import Field

from taskdantic import Task, uda


class MetadataTask(Task):
    metadata_field: str | None = Field(
        default=None,
        json_schema_extra=uda(
            label="Metadata Field",
            type="string",
            values=["alpha", "beta"],
            urgency={"beta": 1.5},
            custom="extra",
        ),
    )


def test_uda_helper_sets_taskwarrior_metadata() -> None:
    field = MetadataTask.model_fields["metadata_field"]
    assert field.json_schema_extra is not None

    taskwarrior = field.json_schema_extra["taskwarrior"]
    assert taskwarrior["label"] == "Metadata Field"
    assert taskwarrior["type"] == "string"
    assert taskwarrior["values"] == ["alpha", "beta"]
    assert taskwarrior["urgency"] == {"beta": 1.5}
    assert taskwarrior["custom"] == "extra"


def test_uda_helper_returns_nested_taskwarrior_key() -> None:
    metadata = uda(label="Label Only")
    assert metadata["taskwarrior"]["label"] == "Label Only"
