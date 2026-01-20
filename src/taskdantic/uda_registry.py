# src/taskdantic/uda_registry.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from taskdantic.models import Task
from taskdantic.uda_export import UdaSpec, extract_uda_specs, merge_uda_specs, render_taskrc_udas


@dataclass(frozen=True)
class UDARegistry:
    specs: dict[str, UdaSpec]

    @classmethod
    def from_task_models(cls, models: Iterable[type[Task]]) -> "UDARegistry":
        spec_map = merge_uda_specs(extract_uda_specs(model) for model in models)
        return cls(specs=spec_map)

    def list(self) -> list[UdaSpec]:
        return sorted(self.specs.values(), key=lambda spec: spec.name)

    def taskrc_block(self) -> str:
        return render_taskrc_udas(self.list())

    def as_prompt_context(self) -> str:
        specs = self.list()
        if not specs:
            return "No Taskwarrior UDAs are registered."

        lines = ["Taskwarrior UDA definitions:"]
        for spec in specs:
            detail = f"- {spec.name} ({spec.type})"
            if spec.label:
                detail += f" label={spec.label}"
            if spec.values:
                detail += f" values={', '.join(spec.values)}"
            if spec.urgency:
                detail += " urgency=" + ", ".join(
                    f"{key}:{value}" for key, value in spec.urgency.items()
                )
            lines.append(detail)
        return "\n".join(lines)
