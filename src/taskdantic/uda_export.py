# src/taskdantic/uda_export.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Iterable, Literal, Union, get_args, get_origin, Annotated

from taskdantic.models import Task

UDA_TYPE_STRING = "string"
UDA_TYPE_NUMERIC = "numeric"
UDA_TYPE_DATE = "date"
UDA_TYPE_DURATION = "duration"


@dataclass(frozen=True)
class UdaSpec:
    name: str
    type: str
    label: str | None = None
    values: list[str] | None = None
    urgency: dict[str, float] | None = None


def _unwrap_annotated(tp: Any) -> Any:
    # typing.Annotated[T, ...] -> T
    if get_origin(tp) is Annotated:
        args = get_args(tp)
        return args[0] if args else tp
    return tp


def _unwrap_optional(tp: Any) -> Any:
    tp = _unwrap_annotated(tp)
    origin = get_origin(tp)
    if origin is Union:
        args = [a for a in get_args(tp) if a is not type(None)]
        if len(args) == 1:
            return _unwrap_annotated(args[0])
    return tp


def _infer_taskwarrior_type(tp: Any) -> str:
    tp = _unwrap_optional(tp)

    if isinstance(tp, type) and issubclass(tp, Enum):
        return UDA_TYPE_STRING

    if get_origin(tp) is Literal:
        return UDA_TYPE_STRING

    if tp is datetime:
        return UDA_TYPE_DATE

    if tp is timedelta:
        return UDA_TYPE_DURATION

    if tp in (int, float):
        return UDA_TYPE_NUMERIC

    return UDA_TYPE_STRING


def _infer_values(tp: Any) -> list[str] | None:
    tp = _unwrap_optional(tp)

    if isinstance(tp, type) and issubclass(tp, Enum):
        return [str(m.value) for m in tp]  # type: ignore[misc]

    if get_origin(tp) is Literal:
        return [str(v) for v in get_args(tp)]

    return None


def _taskwarrior_extra(field: Any) -> dict[str, Any]:
    extra = getattr(field, "json_schema_extra", None) or {}
    return extra.get("taskwarrior", {}) if isinstance(extra, dict) else {}


def extract_uda_specs(task_cls: type[Task]) -> list[UdaSpec]:
    if hasattr(task_cls, "core_field_names"):
        core = task_cls.core_field_names()  # type: ignore[attr-defined]
    else:
        core = set(Task.model_fields.keys())

    computed = set(task_cls.model_computed_fields.keys())
    specs: list[UdaSpec] = []

    for name, field in task_cls.model_fields.items():
        if name in core or name in computed or name.startswith("_"):
            continue

        tw = _taskwarrior_extra(field)
        tp = getattr(field, "annotation", Any)

        uda_type = tw.get("type") or _infer_taskwarrior_type(tp)
        values = tw.get("values") or _infer_values(tp)

        specs.append(
            UdaSpec(
                name=name,
                type=uda_type,
                label=tw.get("label"),
                values=values,
                urgency=tw.get("urgency"),
            )
        )

    return specs


def merge_uda_specs(spec_lists: Iterable[Iterable[UdaSpec]]) -> dict[str, UdaSpec]:
    merged: dict[str, UdaSpec] = {}
    for specs in spec_lists:
        for s in specs:
            if s.name not in merged:
                merged[s.name] = s
                continue

            prev = merged[s.name]
            if (prev.type, prev.label, prev.values, prev.urgency) != (s.type, s.label, s.values, s.urgency):
                raise ValueError(
                    f"Conflicting UDA definition for {s.name!r}: {prev} vs {s}. Ensure all Task subclasses agree."
                )
    return merged


def render_taskrc_udas(specs: Iterable[UdaSpec]) -> str:
    lines: list[str] = []
    for s in sorted(specs, key=lambda x: x.name):
        lines.append(f"uda.{s.name}.type={s.type}")
        if s.label:
            lines.append(f"uda.{s.name}.label={s.label}")
        if s.values:
            lines.append("uda." + s.name + ".values=" + ",".join(s.values))
        if s.urgency:
            for val, coeff in s.urgency.items():
                lines.append(f"urgency.uda.{s.name}.{val}.coefficient={coeff}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
