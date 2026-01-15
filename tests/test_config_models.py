# tests/test_config_models.py

from __future__ import annotations

from pathlib import Path

import pytest

from taskdantic.config import TaskRcParser
from taskdantic.config_models import (
    ConfigOption,
    ConfigSection,
    ConfigValue,
    TaskConfig,
    UDADefinition,
    UDAType,
)
from taskdantic.exceptions import ConfigError


@pytest.mark.unit
class TestConfigValue:
    """Test ConfigValue model for hierarchical config storage."""

    def test_leaf_value(self) -> None:
        """Test creating a leaf value."""
        value = ConfigValue(value="test")
        assert value.is_leaf
        assert not value.is_branch
        assert value.get_leaf_value() == "test"

    def test_branch_value(self) -> None:
        """Test creating a branch with children."""
        value = ConfigValue(
            children={
                "child1": ConfigValue(value="value1"),
                "child2": ConfigValue(value="value2"),
            }
        )
        assert value.is_branch
        assert not value.is_leaf
        assert value.get_child("child1") is not None
        assert value.get_child("child1").get_leaf_value() == "value1"

    def test_merge_leaf_values(self) -> None:
        """Test merging two leaf values."""
        value1 = ConfigValue(value="original")
        value2 = ConfigValue(value="override")
        merged = value1.merge(value2)
        assert merged.get_leaf_value() == "override"

    def test_merge_branch_values(self) -> None:
        """Test merging branches with children."""
        value1 = ConfigValue(
            children={
                "a": ConfigValue(value="original_a"),
                "b": ConfigValue(value="original_b"),
            }
        )
        value2 = ConfigValue(
            children={
                "a": ConfigValue(value="override_a"),
                "c": ConfigValue(value="new_c"),
            }
        )
        merged = value1.merge(value2)
        assert merged.get_child("a").get_leaf_value() == "override_a"
        assert merged.get_child("b").get_leaf_value() == "original_b"
        assert merged.get_child("c").get_leaf_value() == "new_c"

    def test_set_child(self) -> None:
        """Test setting a child value."""
        value = ConfigValue()
        value.set_child("key", ConfigValue(value="test"))
        assert value.get_child("key").get_leaf_value() == "test"


@pytest.mark.unit
class TestConfigOption:
    """Test ConfigOption model for individual config entries."""

    def test_simple_option(self) -> None:
        """Test creating a simple option."""
        option = ConfigOption(key="confirmation", value="off")
        assert option.key == "confirmation"
        assert option.value == "off"
        assert not option.is_nested
        assert option.key_parts == ["confirmation"]

    def test_nested_option(self) -> None:
        """Test creating a nested option."""
        option = ConfigOption(key="data.location", value="/home/user/.task")
        assert option.is_nested
        assert option.key_parts == ["data", "location"]

    def test_matches_prefix(self) -> None:
        """Test prefix matching."""
        option = ConfigOption(key="color.active", value="blue")
        assert option.matches_prefix("color")
        assert option.matches_prefix("color.active")
        assert not option.matches_prefix("data")

    def test_uda_option(self) -> None:
        """Test UDA option."""
        option = ConfigOption(key="uda.estimate.type", value="numeric", is_uda=True)
        assert option.is_uda
        assert option.matches_prefix("uda")


@pytest.mark.unit
class TestConfigSection:
    """Test ConfigSection for grouping related options."""

    def test_create_section(self) -> None:
        """Test creating a config section."""
        section = ConfigSection(prefix="color")
        option1 = ConfigOption(key="color.active", value="blue")
        option2 = ConfigOption(key="color.due", value="red")
        section.add_option(option1)
        section.add_option(option2)
        assert len(section.options) == 2

    def test_section_to_dict(self) -> None:
        """Test converting section to dict."""
        section = ConfigSection(prefix="color")
        section.add_option(ConfigOption(key="color.active", value="blue"))
        section.add_option(ConfigOption(key="color.due", value="red"))
        result = section.to_dict()
        assert result["color.active"] == "blue"
        assert result["color.due"] == "red"

    def test_get_option(self) -> None:
        """Test retrieving option from section."""
        section = ConfigSection(prefix="color")
        option = ConfigOption(key="color.active", value="blue")
        section.add_option(option)
        retrieved = section.get_option("color.active")
        assert retrieved is not None
        assert retrieved.value == "blue"


@pytest.mark.unit
class TestUDADefinition:
    """Test UDADefinition model."""

    def test_create_uda(self) -> None:
        """Test creating a UDA definition."""
        uda = UDADefinition(name="estimate", type=UDAType.NUMERIC, label="Estimate")
        assert uda.name == "estimate"
        assert uda.type == UDAType.NUMERIC
        assert uda.label == "Estimate"
        assert not uda.is_choice

    def test_uda_with_values(self) -> None:
        """Test UDA with choice values."""
        uda = UDADefinition(
            name="complexity",
            type=UDAType.STRING,
            values=["low", "medium", "high"],
        )
        assert uda.is_choice
        assert len(uda.values) == 3

    def test_uda_type_validation(self) -> None:
        """Test UDA type validation from string."""
        uda = UDADefinition(name="test", type="numeric")
        assert uda.type == UDAType.NUMERIC

    def test_uda_to_dict(self) -> None:
        """Test converting UDA to dict."""
        uda = UDADefinition(
            name="complexity",
            type=UDAType.STRING,
            label="Complexity",
            values=["low", "high"],
        )
        result = uda.to_dict()
        assert result["type"] == "string"
        assert result["label"] == "Complexity"
        assert result["values"] == "low,high"


@pytest.mark.unit
class TestTaskConfig:
    """Test TaskConfig composition model."""

    def test_empty_config(self) -> None:
        """Test creating empty config."""
        config = TaskConfig()
        assert config.values == {}
        assert config.udas == {}
        assert config.options == []

    def test_add_option(self) -> None:
        """Test adding options to config."""
        config = TaskConfig()
        config.add_option(ConfigOption(key="confirmation", value="off"))
        assert len(config.options) == 1
        assert config.get("confirmation") == "off"

    def test_nested_key_storage(self) -> None:
        """Test storing nested keys."""
        config = TaskConfig()
        config.add_option(ConfigOption(key="data.location", value="/home/user/.task"))
        config.add_option(ConfigOption(key="color.active", value="blue"))
        config.add_option(ConfigOption(key="color.due", value="red"))

        assert config.get("data.location") == "/home/user/.task"
        assert config.get("color.active") == "blue"
        assert config.get("color.due") == "red"

    def test_get_section(self) -> None:
        """Test retrieving a config section."""
        config = TaskConfig()
        config.add_option(ConfigOption(key="color.active", value="blue"))
        config.add_option(ConfigOption(key="color.due", value="red"))
        config.add_option(ConfigOption(key="data.location", value="/home/.task"))

        color_section = config.get_section("color")
        assert color_section["active"] == "blue"
        assert color_section["due"] == "red"
        assert "location" not in color_section

    def test_both_value_and_children(self) -> None:
        """Test handling both a value and children (taskw limitation case)."""
        config = TaskConfig()
        config.add_option(ConfigOption(key="color", value="on"))
        config.add_option(ConfigOption(key="color.header", value="blue"))

        assert config.get("color") == "on"
        assert config.get("color.header") == "blue"

    def test_merge_configs(self) -> None:
        """Test merging two configs."""
        config1 = TaskConfig()
        config1.add_option(ConfigOption(key="confirmation", value="on"))
        config1.add_option(ConfigOption(key="color.active", value="blue"))

        config2 = TaskConfig()
        config2.add_option(ConfigOption(key="confirmation", value="off"))
        config2.add_option(ConfigOption(key="color.due", value="red"))

        merged = config1.merge(config2)
        assert merged.get("confirmation") == "off"
        assert merged.get("color.active") == "blue"
        assert merged.get("color.due") == "red"

    def test_get_all_options_with_prefix(self) -> None:
        """Test getting all options matching a prefix."""
        config = TaskConfig()
        config.add_option(ConfigOption(key="color.active", value="blue"))
        config.add_option(ConfigOption(key="color.due", value="red"))
        config.add_option(ConfigOption(key="data.location", value="/home/.task"))

        color_options = config.get_all_options_with_prefix("color")
        assert len(color_options) == 2
        assert all(opt.key.startswith("color") for opt in color_options)


@pytest.mark.unit
class TestTaskRcParser:
    """Test TaskRcParser with new models."""

    def test_parse_simple_config(self, temp_dir: Path) -> None:
        """Test parsing simple config file."""
        config_file = temp_dir / ".taskrc"
        config_file.write_text(
            """
data.location=/home/user/.task
confirmation=off
verbose=yes
"""
        )

        parser = TaskRcParser(config_file)
        config = parser.parse()

        assert config.get("data.location") == "/home/user/.task"
        assert config.get("confirmation") == "off"
        assert config.get("verbose") == "yes"

    def test_parse_with_comments(self, temp_dir: Path) -> None:
        """Test that comments are ignored."""
        config_file = temp_dir / ".taskrc"
        config_file.write_text(
            """
# This is a comment
data.location=/home/user/.task
confirmation=off  # inline comment
# Another comment
"""
        )

        parser = TaskRcParser(config_file)
        config = parser.parse()
        assert len(config.options) == 2

    def test_parse_nested_config(self, temp_dir: Path) -> None:
        """Test parsing nested configuration."""
        config_file = temp_dir / ".taskrc"
        config_file.write_text(
            """
color.active=rgb555 on rgb410
color.due=rgb550
report.next.filter=status:pending -WAITING
"""
        )

        parser = TaskRcParser(config_file)
        config = parser.parse()

        assert config.get("color.active") == "rgb555 on rgb410"
        assert config.get("color.due") == "rgb550"
        assert config.get("report.next.filter") == "status:pending -WAITING"

    def test_parse_udas(self, temp_dir: Path) -> None:
        """Test parsing UDA definitions."""
        config_file = temp_dir / ".taskrc"
        config_file.write_text(
            """
uda.estimate.type=numeric
uda.estimate.label=Estimate
uda.complexity.type=string
uda.complexity.label=Complexity
uda.complexity.values=low,medium,high
"""
        )

        parser = TaskRcParser(config_file)
        config = parser.parse()

        assert "estimate" in config.udas
        assert config.udas["estimate"].type == UDAType.NUMERIC
        assert config.udas["estimate"].label == "Estimate"

        assert "complexity" in config.udas
        assert config.udas["complexity"].type == UDAType.STRING
        assert config.udas["complexity"].is_choice
        assert len(config.udas["complexity"].values) == 3

    def test_parse_with_includes(self, temp_dir: Path) -> None:
        """Test parsing config with include directives."""
        include_file = temp_dir / "included.taskrc"
        include_file.write_text("verbose=yes\ncolor.active=blue")

        main_file = temp_dir / ".taskrc"
        main_file.write_text(
            f"""
data.location=/home/user/.task
include {include_file}
confirmation=off
"""
        )

        parser = TaskRcParser(main_file)
        config = parser.parse()

        assert config.get("data.location") == "/home/user/.task"
        assert config.get("verbose") == "yes"
        assert config.get("color.active") == "blue"
        assert config.get("confirmation") == "off"

    def test_parse_with_quotes(self, temp_dir: Path) -> None:
        """Test parsing values with quotes."""
        config_file = temp_dir / ".taskrc"
        config_file.write_text(
            """
key1="value with spaces"
key2='another value'
key3=no quotes
"""
        )

        parser = TaskRcParser(config_file)
        config = parser.parse()

        assert config.get("key1") == "value with spaces"
        assert config.get("key2") == "another value"
        assert config.get("key3") == "no quotes"

    def test_parse_empty_value(self, temp_dir: Path) -> None:
        """Test parsing config with empty value."""
        config_file = temp_dir / ".taskrc"
        config_file.write_text("context=\n")

        parser = TaskRcParser(config_file)
        config = parser.parse()
        assert config.get("context") == ""

    def test_parse_malformed_line(self, temp_dir: Path) -> None:
        """Test that malformed lines are skipped."""
        config_file = temp_dir / ".taskrc"
        config_file.write_text(
            """
data.location=/home/user/.task
this-line-has-no-equals
confirmation=off
"""
        )

        parser = TaskRcParser(config_file)
        config = parser.parse()
        assert len(config.options) == 2

    def test_parse_nonexistent_file(self) -> None:
        """Test that nonexistent file raises ConfigError."""
        with pytest.raises(ConfigError):
            TaskRcParser("/nonexistent/file.taskrc")

    def test_value_and_children_coexist(self, temp_dir: Path) -> None:
        """Test that both parent value and children can exist (unlike taskw)."""
        config_file = temp_dir / ".taskrc"
        config_file.write_text(
            """
color=on
color.active=blue
color.due=red
"""
        )

        parser = TaskRcParser(config_file)
        config = parser.parse()

        assert config.get("color") == "on"
        assert config.get("color.active") == "blue"
        assert config.get("color.due") == "red"

        color_section = config.get_section("color")
        assert "active" in color_section
        assert "due" in color_section
