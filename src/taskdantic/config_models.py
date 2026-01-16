# src/taskdantic/config_models.py

from __future__ import annotations

import yaml
import tempfile

from enum import Enum
from pathlib import Path
from typing import Any, Optional


from pydantic import BaseModel, Field, field_validator


class UDAType(str, Enum):
    """Types for User-Defined Attributes."""

    DATE = "date"
    DURATION = "duration"
    NUMERIC = "numeric"
    STRING = "string"


class ColorConfig(BaseModel):
    """Color configuration with foreground and optional background."""

    foreground: str
    background: Optional[str] = None

    def to_taskrc_value(self) -> str:
        """Convert to .taskrc format: 'foreground on background' or 'foreground'."""
        if self.background:
            return f"{self.foreground} on {self.background}"
        return self.foreground

    @classmethod
    def from_taskrc_value(cls, value: str) -> ColorConfig:
        """Parse from .taskrc format."""
        if " on " in value:
            parts = value.split(" on ", 1)
            return cls(foreground=parts[0].strip(), background=parts[1].strip())
        return cls(foreground=value.strip())

    @classmethod
    def from_string(cls, value: str) -> ColorConfig:
        """Alias for from_taskrc_value for convenience."""
        return cls.from_taskrc_value(value)


class ReportConfig(BaseModel):
    """Report configuration with filter, columns, labels, sort, and description."""

    columns: str
    labels: str
    filter: str
    sort: Optional[str] = None
    description: Optional[str] = None

    def to_taskrc_dict(self, report_name: str) -> dict[str, str]:
        """Convert to flat .taskrc key-value pairs."""
        result = {
            f"report.{report_name}.columns": self.columns,
            f"report.{report_name}.labels": self.labels,
            f"report.{report_name}.filter": self.filter,
        }
        if self.sort:
            result[f"report.{report_name}.sort"] = self.sort
        if self.description:
            result[f"report.{report_name}.description"] = self.description
        return result


class UrgencyConfig(BaseModel):
    """Urgency coefficient configuration."""

    coefficient: float

    def to_taskrc_value(self) -> str:
        """Convert to .taskrc format."""
        return str(self.coefficient)


class ContextConfig(BaseModel):
    """Context filter configuration."""

    filter: str

    def to_taskrc_value(self) -> str:
        """Convert to .taskrc format."""
        return self.filter


class UDADefinition(BaseModel):
    """User-Defined Attribute definition from taskrc."""

    name: str
    type: UDAType
    label: Optional[str] = None
    values: Optional[list[str]] = None
    source_file: Optional[Path] = None

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, value: Any) -> UDAType:
        """Validate and convert UDA type."""
        if isinstance(value, UDAType):
            return value
        if isinstance(value, str):
            try:
                return UDAType(value.lower())
            except ValueError:
                return UDAType.STRING
        return UDAType.STRING

    @property
    def is_choice(self) -> bool:
        """Check if this UDA is a choice field."""
        return self.values is not None and len(self.values) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for compatibility."""
        result: dict[str, Any] = {
            "type": self.type.value,
        }
        if self.label:
            result["label"] = self.label
        if self.values:
            result["values"] = ",".join(self.values)
        return result


class ConfigValue(BaseModel):
    """Represents a configuration value that can be simple or nested."""

    value: Optional[str] = None
    children: dict[str, ConfigValue] = Field(default_factory=dict)
    source_file: Optional[Path] = None

    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf value (no children)."""
        return len(self.children) == 0

    @property
    def is_branch(self) -> bool:
        """Check if this has children."""
        return len(self.children) > 0

    def get_leaf_value(self) -> Optional[str]:
        """Get the leaf value if this is a leaf node."""
        if self.is_leaf:
            return self.value
        return None

    def get_child(self, key: str) -> Optional[ConfigValue]:
        """Get a child value by key."""
        return self.children.get(key)

    def set_child(self, key: str, value: ConfigValue) -> None:
        """Set a child value."""
        self.children[key] = value

    def merge(self, other: ConfigValue) -> ConfigValue:
        """Merge another ConfigValue into this one, with other taking precedence."""
        if other.is_leaf:
            return ConfigValue(
                value=other.value,
                source_file=other.source_file or self.source_file,
            )

        merged_children = self.children.copy()
        for key, child_value in other.children.items():
            if key in merged_children:
                merged_children[key] = merged_children[key].merge(child_value)
            else:
                merged_children[key] = child_value

        return ConfigValue(
            value=other.value if other.value is not None else self.value,
            children=merged_children,
            source_file=other.source_file or self.source_file,
        )


class ConfigOption(BaseModel):
    """Single configuration option with its full key path."""

    key: str
    value: Optional[str] = None
    source_file: Optional[Path] = None
    is_uda: bool = False

    @property
    def key_parts(self) -> list[str]:
        """Split key into parts using dot notation."""
        return self.key.split(".")

    @property
    def is_nested(self) -> bool:
        """Check if this key represents a nested configuration."""
        return "." in self.key

    def matches_prefix(self, prefix: str) -> bool:
        """Check if this option's key starts with the given prefix."""
        return self.key.startswith(prefix)


class ConfigSection(BaseModel):
    """A section of related configuration options."""

    prefix: str
    options: list[ConfigOption] = Field(default_factory=list)

    def add_option(self, option: ConfigOption) -> None:
        """Add an option to this section."""
        if option.matches_prefix(self.prefix):
            self.options.append(option)

    def get_option(self, key: str) -> Optional[ConfigOption]:
        """Get an option by its full key."""
        for option in self.options:
            if option.key == key:
                return option
        return None

    def to_dict(self) -> dict[str, str]:
        """Convert section to dictionary."""
        return {opt.key: opt.value or "" for opt in self.options if opt.value is not None}


class TaskConfig(BaseModel):
    """Complete Taskwarrior configuration composed of ConfigValue tree and UDAs."""

    data_location: Optional[str] = Field(None, alias="data.location")
    udas: dict[str, UDADefinition] = Field(default_factory=dict)
    values: dict[str, ConfigValue] = Field(default_factory=dict)
    options: list[ConfigOption] = Field(default_factory=list)
    source_files: list[Path] = Field(default_factory=list)

    def add_option(self, option: ConfigOption) -> None:
        """Add a configuration option and update the value tree."""
        self.options.append(option)
        self._add_to_tree(option.key, option.value, option.source_file)

    def _add_to_tree(self, key: str, value: Optional[str], source_file: Optional[Path]) -> None:
        """Add a key-value pair to the hierarchical tree structure."""
        parts = key.split(".")
        current = self.values

        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = ConfigValue()
            if current[part].is_leaf and current[part].value is not None:
                # Preserve existing value when converting to branch
                current[part] = ConfigValue(
                    value=current[part].value,
                    children={},
                    source_file=current[part].source_file,
                )
            elif current[part].is_leaf:
                current[part] = ConfigValue(children={})
            current = current[part].children

        final_key = parts[-1]
        if final_key not in current:
            current[final_key] = ConfigValue(value=value, source_file=source_file)
        elif current[final_key].is_leaf:
            current[final_key] = ConfigValue(value=value, source_file=source_file)
        else:
            # Branch exists, set value on it
            current[final_key].value = value
            if source_file:
                current[final_key].source_file = source_file

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-notation key.

        Handles both leaf nodes and branch nodes that have their own value.
        Example: color=on and color.active=blue both exist.
        """
        parts = key.split(".")
        current_dict = self.values
        current_value = None

        for part in parts:
            if part not in current_dict:
                return default
            current_value = current_dict[part]
            if current_value.is_leaf:
                return current_value.value if current_value.value is not None else default
            current_dict = current_value.children

        # After traversing, check if we have a branch node with a value
        if current_value is not None and current_value.value is not None:
            return current_value.value
        return default

    def get_section(self, prefix: str) -> dict[str, Any]:
        """Get all configuration values under a prefix as a nested dict."""
        parts = prefix.split(".")
        current_dict = self.values

        for part in parts:
            if part not in current_dict:
                return {}
            current_value = current_dict[part]
            if current_value.is_leaf:
                return {}
            current_dict = current_value.children

        return self._build_dict_from_values(current_dict)

    def _build_dict_from_values(self, values: dict[str, ConfigValue]) -> dict[str, Any]:
        """Recursively build a dictionary from ConfigValue tree."""
        result: dict[str, Any] = {}
        for key, value in values.items():
            if value.is_leaf:
                result[key] = value.value
            else:
                child_dict = self._build_dict_from_values(value.children)
                if value.value is not None:
                    result[key] = value.value
                if child_dict:
                    if key in result and not isinstance(result[key], dict):
                        pass
                    else:
                        result[key] = child_dict
        return result

    def get_all_options_with_prefix(self, prefix: str) -> list[ConfigOption]:
        """Get all options that match a given prefix."""
        return [opt for opt in self.options if opt.matches_prefix(prefix)]

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> TaskConfig:
        """Load TaskConfig from YAML file.

        Args:
            yaml_path: Path to YAML config file

        Returns:
            TaskConfig instance with hierarchical structure
        """
        path = Path(yaml_path).expanduser()
        if not path.exists():
            return cls()

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        config = cls()

        # Process UDAs first
        udas_dict = data.pop("udas", {})
        for name, uda_data in udas_dict.items():
            if isinstance(uda_data, dict):
                uda_type = uda_data.get("type", "string")
                uda_label = uda_data.get("label")
                uda_values = uda_data.get("values")

                config.udas[name] = UDADefinition(
                    name=name,
                    type=uda_type,
                    label=uda_label,
                    values=uda_values,
                )

        # Process remaining config into hierarchical structure
        cls._process_dict_to_config(config, data, "")

        # Extract data.location
        config.data_location = config.get("data.location")

        return config

    def _to_yaml_dict(self) -> dict[str, Any]:
        """Convert hierarchical structure back to YAML dict."""
        result: dict[str, Any] = {}

        for key, value in self.values.items():
            if value.is_leaf:
                result[key] = self._parse_value(value.value)
            else:
                child_dict = self._build_dict_from_values(value.children)
                if value.value is not None:
                    result[key] = self._parse_value(value.value)
                if child_dict:
                    if isinstance(result.get(key), dict):
                        result[key].update(child_dict)
                    else:
                        result[key] = child_dict

        return result

    @staticmethod
    def _parse_value(value: Optional[str]) -> Any:
        """Parse string value back to Python types."""
        if value is None or value == "":
            return None
        elif value == "on":
            return True
        elif value == "off":
            return False
        elif "," in value:
            return value.split(",")
        else:
            # Try to parse as number
            try:
                if "." in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                return value

    @classmethod
    def _process_dict_to_config(cls, config: TaskConfig, data: dict[str, Any], prefix: str) -> None:
        """Recursively process dictionary into ConfigOptions."""
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                cls._process_dict_to_config(config, value, full_key)
            else:
                str_value = cls._convert_value_to_string(value)
                option = ConfigOption(key=full_key, value=str_value)
                config.add_option(option)

    @staticmethod
    def _convert_value_to_string(value: Any) -> str:
        """Convert Python value to taskrc string format."""
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "on" if value else "off"
        elif isinstance(value, list):
            return ",".join(str(v) for v in value)
        else:
            return str(value)

    def merge(self, other: TaskConfig) -> TaskConfig:
        """Merge another TaskConfig into this one, with other taking precedence."""
        merged_values = {}
        for key, value in self.values.items():
            if key in other.values:
                merged_values[key] = value.merge(other.values[key])
            else:
                merged_values[key] = value

        for key, value in other.values.items():
            if key not in merged_values:
                merged_values[key] = value

        merged_udas = {**self.udas, **other.udas}

        merged_options = self.options.copy()
        other_keys = {opt.key for opt in other.options}
        merged_options = [opt for opt in merged_options if opt.key not in other_keys]
        merged_options.extend(other.options)

        merged_source_files = list(set(self.source_files + other.source_files))

        return TaskConfig(
            data_location=other.data_location or self.data_location,
            udas=merged_udas,
            values=merged_values,
            options=merged_options,
            source_files=merged_source_files,
        )

    def get_udas(self) -> dict[str, dict[str, Any]]:
        """Get all UDA definitions as a dict for compatibility."""
        return {name: uda.to_dict() for name, uda in self.udas.items()}

    def get_colors(self) -> dict[str, ColorConfig]:
        """Get all color configurations."""
        colors = {}
        for opt in self.get_all_options_with_prefix("color."):
            if opt.value:
                color_key = opt.key.replace("color.", "")
                colors[color_key] = ColorConfig.from_taskrc_value(opt.value)
        return colors

    def get_reports(self) -> dict[str, ReportConfig]:
        """Get all report configurations."""
        reports: dict[str, dict[str, str]] = {}
        for opt in self.get_all_options_with_prefix("report."):
            parts = opt.key.split(".")
            if len(parts) >= 3:
                report_name = parts[1]
                field_name = ".".join(parts[2:])
                if report_name not in reports:
                    reports[report_name] = {}
                if opt.value:
                    reports[report_name][field_name] = opt.value

        # Convert to ReportConfig objects
        report_configs = {}
        for name, fields in reports.items():
            if "columns" in fields and "labels" in fields and "filter" in fields:
                report_configs[name] = ReportConfig(
                    columns=fields["columns"],
                    labels=fields["labels"],
                    filter=fields["filter"],
                    sort=fields.get("sort"),
                    description=fields.get("description"),
                )
        return report_configs

    def write_taskrc(self, output_path: str | Path) -> None:
        """Write configuration to .taskrc format.

        Args:
            output_path: Path where .taskrc should be written
        """
        from taskdantic.config_writer import TaskRcWriter

        # Reconstruct full config dict for TaskRcWriter
        full_config = self._to_yaml_dict()

        if self.udas:
            full_config["udas"] = {
                name: {
                    "type": uda.type.value,
                    **({"label": uda.label} if uda.label else {}),
                    **({"values": uda.values} if uda.values else {}),
                }
                for name, uda in self.udas.items()
            }

        # Write to temporary YAML then convert
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(full_config, f)
            temp_yaml = f.name

        try:
            writer = TaskRcWriter(temp_yaml)
            writer.write_taskrc(output_path)
        finally:
            Path(temp_yaml).unlink(missing_ok=True)

    @classmethod
    def from_file(cls, path: str | Path) -> TaskConfig:
        """Load TaskConfig from a .taskrc file."""
        from pathlib import Path

        from taskdantic.config import TaskRcParser
        from taskdantic.exceptions import ConfigError

        try:
            parser = TaskRcParser(Path(path))
            return parser.parse()
        except ConfigError:
            return cls()
