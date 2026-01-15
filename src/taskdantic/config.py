# src/taskdantic/config.py

from __future__ import annotations

from pathlib import Path
from typing import Any

from taskdantic.config_models import (
    ConfigOption,
    TaskConfig,
    UDADefinition,
    UDAType,
)
from taskdantic.exceptions import ConfigError


def sanitize_line(line: str) -> str:
    """Remove comments and whitespace from a config line."""
    comment_position = line.find("#")
    if comment_position >= 0:
        line = line[:comment_position]
    return line.strip()


class TaskRcParser:
    """Parse Taskwarrior configuration files into Pydantic models."""

    def __init__(self, path: str | Path):
        """Initialize parser with path to taskrc file."""
        self.path = Path(path).expanduser().resolve()
        if not self.path.exists():
            raise ConfigError(f"Config file not found: {self.path}")

    def parse(self) -> TaskConfig:
        """Parse taskrc file into TaskConfig model."""
        config = TaskConfig(source_files=[self.path])
        self._parse_file(self.path, config)
        self._extract_data_location(config)
        return config

    def _parse_file(self, path: Path, config: TaskConfig, visited: set[Path] | None = None) -> None:
        """Parse a single taskrc file, handling includes recursively."""
        if visited is None:
            visited = set()

        resolved_path = path.resolve()
        if resolved_path in visited:
            return

        visited.add(resolved_path)

        try:
            with open(path, encoding="utf-8") as f:
                for line_num, raw_line in enumerate(f, 1):
                    try:
                        self._parse_line(raw_line, path, config, visited)
                    except Exception as e:
                        raise ConfigError(
                            f"Error parsing line {line_num} in {path}: {raw_line.strip()}"
                        ) from e
        except OSError as e:
            raise ConfigError(f"Failed to read config file {path}: {e}") from e

    def _parse_line(
        self,
        line: str,
        source_file: Path,
        config: TaskConfig,
        visited: set[Path],
    ) -> None:
        """Parse a single line from taskrc file."""
        line = sanitize_line(line)

        if not line:
            return

        if line.startswith("include "):
            self._handle_include(line, source_file, config, visited)
            return

        if "=" not in line:
            return

        key, _, value = line.partition("=")
        key = key.strip()
        value = self._clean_value(value.strip())

        if not key:
            return

        option = ConfigOption(
            key=key,
            value=value,
            source_file=source_file,
            is_uda=key.startswith("uda."),
        )

        if option.is_uda:
            self._process_uda_option(option, config)

        config.add_option(option)

    def _handle_include(
        self,
        line: str,
        source_file: Path,
        config: TaskConfig,
        visited: set[Path],
    ) -> None:
        """Handle include directive."""
        include_path_str = line[8:].strip()
        if not include_path_str:
            return

        include_path = Path(include_path_str).expanduser()

        if not include_path.is_absolute():
            include_path = (source_file.parent / include_path).resolve()

        if not include_path.exists():
            return

        # Parse the included file directly into a temporary config
        included_config = TaskConfig(source_files=[include_path])
        self._parse_file(include_path, included_config, visited)

        # Merge included config into main config
        for option in included_config.options:
            config.add_option(option)
        
        for name, uda in included_config.udas.items():
            config.udas[name] = uda
        
        if include_path not in config.source_files:
            config.source_files.append(include_path)

    def _clean_value(self, value: str) -> str:
        """Remove quotes from config values."""
        if len(value) >= 2:
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                return value[1:-1]
        return value

    def _process_uda_option(self, option: ConfigOption, config: TaskConfig) -> None:
        """Process a UDA configuration option."""
        parts = option.key.split(".")
        if len(parts) < 3:
            return

        uda_name = parts[1]
        uda_property = parts[2]

        if uda_name not in config.udas:
            config.udas[uda_name] = UDADefinition(
                name=uda_name,
                type=UDAType.STRING,
                source_file=option.source_file,
            )

        uda = config.udas[uda_name]

        if uda_property == "type" and option.value:
            try:
                uda.type = UDAType(option.value.lower())
            except ValueError:
                uda.type = UDAType.STRING

        elif uda_property == "label" and option.value:
            uda.label = option.value

        elif uda_property == "values" and option.value:
            uda.values = [v.strip() for v in option.value.split(",") if v.strip()]

    def _extract_data_location(self, config: TaskConfig) -> None:
        """Extract data.location if present."""
        data_location = config.get("data.location")
        if data_location:
            config.data_location = data_location
