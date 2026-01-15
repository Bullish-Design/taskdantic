# src/taskdantic/config_writer.py

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class TaskRcWriter:
    """Write YAML configuration to .taskrc format."""

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
        "udas": {},
    }

    output = Path(output_path).expanduser()
    with open(output, "w", encoding="utf-8") as f:
        yaml.safe_dump(default_config, f, default_flow_style=False, sort_keys=False)
