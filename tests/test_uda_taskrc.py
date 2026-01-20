# tests/test_uda_taskrc.py
from __future__ import annotations

from taskdantic.uda_taskrc import BEGIN_MARKER, END_MARKER, parse_existing_uda_names, upsert_uda_block


def test_parse_existing_uda_names() -> None:
    taskrc_text = """
    # Example taskrc
    uda.alpha.type=string
    uda.beta.type=numeric
    uda.beta.label=Beta Label

    # Another entry
    uda.gamma.type=date
    """

    names = parse_existing_uda_names(taskrc_text)

    assert names == {"alpha", "beta", "gamma"}


def test_upsert_uda_block_inserts_when_missing() -> None:
    original = "include ~/.taskrc\n"
    block_body = "uda.alpha.type=string\n"

    updated = upsert_uda_block(original, block_body)

    assert BEGIN_MARKER in updated
    assert END_MARKER in updated
    assert "uda.alpha.type=string" in updated
    assert updated.startswith(original)


def test_upsert_uda_block_replaces_existing_block() -> None:
    original = (
        "tag.color=blue\n\n"
        f"{BEGIN_MARKER}\n"
        "# Generated from Pydantic Task models. Do not edit by hand.\n\n"
        "uda.old.type=string\n"
        f"{END_MARKER}\n\n"
        "report.list.columns=id,description\n"
    )
    block_body = "uda.new.type=numeric\n"

    updated = upsert_uda_block(original, block_body)

    assert "uda.old.type=string" not in updated
    assert "uda.new.type=numeric" in updated
    assert updated.splitlines()[0] == "tag.color=blue"
    assert updated.strip().endswith("report.list.columns=id,description")
