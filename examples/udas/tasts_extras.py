from __future__ import annotations

from taskdantic import Task


class BareTask(Task):
    """
    Intentionally no typed UDAs here.
    Useful to test runtime extras still work as UDAs.
    """

    pass


def make_task_with_runtime_uda() -> Task:
    # Since Task config allows extra fields, this should still be treated as a UDA
    return BareTask(description="Runtime UDA test", foo_bar="baz")  # type: ignore[arg-type]
