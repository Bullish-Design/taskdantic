# src/taskdantic/config_models.py

from __future__ import annotations

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
        """Get a configuration value by dot-notation key."""
        parts = key.split(".")
        current_dict = self.values

        for part in parts:
            if part not in current_dict:
                return default
            current_value = current_dict[part]
            if current_value.is_leaf:
                return current_value.value if current_value.value is not None else default
            current_dict = current_value.children

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
