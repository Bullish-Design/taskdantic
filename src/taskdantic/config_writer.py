# src/taskdantic/config_writer.py

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class TaskRcWriter:
    """Write YAML configuration to .taskrc format with support for structured models."""

    def __init__(self, yaml_path: str | Path):
        """Initialize writer with YAML config path."""
        self.yaml_path = Path(yaml_path).expanduser()

    def load_yaml(self) -> dict[str, Any]:
        """Load YAML configuration file."""
        with open(self.yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def write_taskrc(self, output_path: str | Path) -> None:
        """Write YAML config to .taskrc format.

        Args:
            output_path: Path where .taskrc should be written
        """
        config = self.load_yaml()
        output = Path(output_path).expanduser()

        lines = ["# Generated from taskdantic YAML configuration", ""]
        lines.extend(self._convert_to_taskrc(config))

        output.write_text("\n".join(lines))

    def _convert_to_taskrc(self, config: dict[str, Any], prefix: str = "") -> list[str]:
        """Convert nested dict to flat key=value lines.

        Args:
            config: Configuration dictionary
            prefix: Current key prefix for nested values

        Returns:
            List of key=value lines
        """
        lines: list[str] = []

        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key

            # Handle special structured sections
            if key == "colors" and isinstance(value, dict):
                lines.extend(self._write_colors(value))
                continue

            if key == "reports" and isinstance(value, dict):
                lines.extend(self._write_reports(value))
                continue

            if key == "contexts" and isinstance(value, dict):
                lines.extend(self._write_contexts(value))
                continue

            if key == "defaults" and isinstance(value, dict):
                lines.extend(self._write_defaults(value))
                continue

            # Handle UDAs specially
            if key == "udas" and isinstance(value, dict):
                lines.extend(self._write_udas(value))
                continue

            # Handle nested dicts
            if isinstance(value, dict):
                lines.extend(self._convert_to_taskrc(value, full_key))
            # Handle lists (for UDA values)
            elif isinstance(value, list):
                lines.append(f"{full_key}={','.join(str(v) for v in value)}")
            # Handle booleans
            elif isinstance(value, bool):
                lines.append(f"{full_key}={'on' if value else 'off'}")
            # Handle None
            elif value is None:
                lines.append(f"{full_key}=")
            # Handle strings and numbers
            else:
                lines.append(f"{full_key}={value}")

        return lines

    def _write_colors(self, colors: dict[str, Any]) -> list[str]:
        """Write color definitions in .taskrc format.

        Args:
            colors: Color definitions dict (can be strings or dicts with fg/bg)

        Returns:
            List of color configuration lines
        """
        lines: list[str] = []

        for color_name, color_config in colors.items():
            if isinstance(color_config, dict):
                # Structured format: {foreground: X, background: Y}
                fg = color_config.get("foreground", "")
                bg = color_config.get("background")
                if bg:
                    lines.append(f"color.{color_name}={fg} on {bg}")
                else:
                    lines.append(f"color.{color_name}={fg}")
            elif isinstance(color_config, str):
                # Simple string format
                lines.append(f"color.{color_name}={color_config}")

        return lines

    def _write_reports(self, reports: dict[str, Any]) -> list[str]:
        """Write report definitions in .taskrc format.

        Args:
            reports: Report definitions dict

        Returns:
            List of report configuration lines
        """
        lines: list[str] = []

        for report_name, report_config in reports.items():
            if not isinstance(report_config, dict):
                continue

            # Required fields
            if "columns" in report_config:
                lines.append(f"report.{report_name}.columns={report_config['columns']}")
            if "labels" in report_config:
                lines.append(f"report.{report_name}.labels={report_config['labels']}")
            if "filter" in report_config:
                lines.append(f"report.{report_name}.filter={report_config['filter']}")

            # Optional fields
            if "sort" in report_config:
                lines.append(f"report.{report_name}.sort={report_config['sort']}")
            if "description" in report_config:
                lines.append(f"report.{report_name}.description={report_config['description']}")

        return lines

    def _write_contexts(self, contexts: dict[str, Any]) -> list[str]:
        """Write context definitions in .taskrc format.

        Args:
            contexts: Context definitions dict

        Returns:
            List of context configuration lines
        """
        lines: list[str] = []

        for context_name, context_config in contexts.items():
            if isinstance(context_config, dict) and "filter" in context_config:
                lines.append(f"context.{context_name}={context_config['filter']}")
            elif isinstance(context_config, str):
                lines.append(f"context.{context_name}={context_config}")

        return lines

    def _write_defaults(self, defaults: dict[str, Any]) -> list[str]:
        """Write default settings in .taskrc format.

        Args:
            defaults: Default settings dict

        Returns:
            List of default configuration lines
        """
        lines: list[str] = []

        for key, value in defaults.items():
            lines.append(f"default.{key}={value}")

        return lines

    def _write_udas(self, udas: dict[str, Any]) -> list[str]:
        """Write UDA definitions in .taskrc format.

        Args:
            udas: UDA definitions dict

        Returns:
            List of UDA configuration lines
        """
        lines: list[str] = []

        for uda_name, uda_config in udas.items():
            if not isinstance(uda_config, dict):
                continue

            # Type is required
            if "type" in uda_config:
                lines.append(f"uda.{uda_name}.type={uda_config['type']}")

            # Label is optional
            if "label" in uda_config:
                lines.append(f"uda.{uda_name}.label={uda_config['label']}")

            # Values for string types
            if "values" in uda_config:
                if isinstance(uda_config["values"], list):
                    values_str = ",".join(uda_config["values"])
                    lines.append(f"uda.{uda_name}.values={values_str}")
                else:
                    lines.append(f"uda.{uda_name}.values={uda_config['values']}")

        return lines


def create_default_yaml(output_path: str | Path) -> None:
    """Create a default YAML configuration file.

    Args:
        output_path: Where to write the default config
    """
    default_config = {
        "data": {"location": str(Path.home() / ".task")},
        "confirmation": False,
        "json": {"array": True},
        "hooks": False,
        "context": None,
        "colors": {
            "active": {"foreground": "white", "background": "green"},
            "completed": {"foreground": "green"},
            "due": {"foreground": "red"},
        },
        "reports": {
            "next": {
                "columns": "id,description,priority",
                "labels": "ID,Description,Priority",
                "filter": "status:pending",
                "sort": "urgency-",
            }
        },
        "udas": {},
    }

    output = Path(output_path).expanduser()
    with open(output, "w", encoding="utf-8") as f:
        yaml.safe_dump(default_config, f, default_flow_style=False, sort_keys=False)
