# src/taskdantic/config.py

from __future__ import annotations

from pathlib import Path
from typing import Any

from taskdantic.exceptions import ConfigError
from taskdantic.models import TaskConfig, UDADefinition


class TaskRcParser:
    """Parse Taskwarrior configuration files (.taskrc)."""

    def __init__(self, path: str | Path):
        """Initialize parser with path to taskrc file."""
        self.path = Path(path).expanduser()
        if not self.path.exists():
            raise ConfigError(f"Config file not found: {self.path}")

    def parse(self) -> TaskConfig:
        """Parse taskrc file into TaskConfig model."""
        config_dict: dict[str, Any] = {}
        self._parse_file(self.path, config_dict)

        # Extract UDA definitions
        udas = self._extract_udas(config_dict)

        # Build nested config structure
        nested_config = self._build_nested_dict(config_dict)

        return TaskConfig(
            data_location=config_dict.get("data.location"),
            udas=udas,
            config=nested_config,
        )

    def _parse_file(self, path: Path, config_dict: dict[str, Any]) -> None:
        """Parse a single taskrc file, handling includes."""
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    self._parse_line(line, path.parent, config_dict)
        except OSError as e:
            raise ConfigError(f"Failed to read config file {path}: {e}") from e

    def _parse_line(
        self,
        line: str,
        base_dir: Path,
        config_dict: dict[str, Any],
    ) -> None:
        """Parse a single line from taskrc file."""
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            return

        # Handle include directive
        if line.startswith("include "):
            include_path = line[8:].strip()
            full_path = (base_dir / include_path).expanduser()
            if full_path.exists():
                self._parse_file(full_path, config_dict)
            return

        # Parse key=value
        if "=" not in line:
            return

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        # Remove quotes from value
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]

        config_dict[key] = value

    def _extract_udas(self, config_dict: dict[str, Any]) -> dict[str, UDADefinition]:
        """Extract UDA definitions from config."""
        udas: dict[str, UDADefinition] = {}

        # Find all UDA definitions (uda.<name>.type)
        for key, value in config_dict.items():
            if key.startswith("uda.") and key.endswith(".type"):
                uda_name = key[4:-5]
                uda_type = value

                # Get label and values if defined
                label_key = f"uda.{uda_name}.label"
                values_key = f"uda.{uda_name}.values"

                label = config_dict.get(label_key)
                values_str = config_dict.get(values_key)
                values = values_str.split(",") if values_str else None

                udas[uda_name] = UDADefinition(
                    type=uda_type,
                    label=label,
                    values=values,
                )

        return udas

    def _build_nested_dict(self, config_dict: dict[str, Any]) -> dict[str, Any]:
        """Build nested dictionary from dot-notation keys."""
        result: dict[str, Any] = {}

        for key, value in config_dict.items():
            parts = key.split(".")
            current = result

            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value

        return result
