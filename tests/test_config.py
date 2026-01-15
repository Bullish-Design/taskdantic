# tests/test_config.py

from __future__ import annotations

from pathlib import Path

import pytest

from taskdantic.config_models import TaskConfig


@pytest.mark.unit
class TestTaskConfig:
    """Test TaskConfig parsing and handling."""

    def test_parse_nonexistent_file(self) -> None:
        """Test parsing non-existent config file returns empty config."""
        config = TaskConfig.from_file("/nonexistent/path/.taskrc")
        assert config.values == {}
        assert config.options == []

    def test_parse_empty_file(self, temp_dir: Path) -> None:
        """Test parsing empty config file."""
        config_file = temp_dir / ".taskrc"
        config_file.write_text("")

        config = TaskConfig.from_file(str(config_file))
        assert config.values == {}
        assert config.options == []

    def test_parse_simple_config(self, temp_dir: Path) -> None:
        """Test parsing simple config file."""
        config_file = temp_dir / ".taskrc"
        config_content = """
data.location=/home/user/.task
confirmation=off
verbose=yes
"""
        config_file.write_text(config_content.strip())

        config = TaskConfig.from_file(str(config_file))
        assert config.get("data.location") == "/home/user/.task"
        assert config.get("confirmation") == "off"
        assert config.get("verbose") == "yes"

    def test_parse_config_with_comments(self, temp_dir: Path) -> None:
        """Test that comments are ignored."""
        config_file = temp_dir / ".taskrc"
        config_content = """
# This is a comment
data.location=/home/user/.task
# Another comment
confirmation=off
"""
        config_file.write_text(config_content.strip())

        config = TaskConfig.from_file(str(config_file))
        assert len(config.options) == 2
        assert config.get("data.location") == "/home/user/.task"

    def test_parse_config_with_equals_in_value(self, temp_dir: Path) -> None:
        """Test parsing config with equals sign in value."""
        config_file = temp_dir / ".taskrc"
        config_content = "report.next.filter=status:pending priority:H"
        config_file.write_text(config_content)

        config = TaskConfig.from_file(str(config_file))
        assert config.get("report.next.filter") == "status:pending priority:H"

    def test_parse_config_with_empty_value(self, temp_dir: Path) -> None:
        """Test parsing config with empty value."""
        config_file = temp_dir / ".taskrc"
        config_content = "context="
        config_file.write_text(config_content)

        config = TaskConfig.from_file(str(config_file))
        assert config.get("context") == ""

    def test_parse_config_with_spaces(self, temp_dir: Path) -> None:
        """Test parsing config with spaces around equals."""
        config_file = temp_dir / ".taskrc"
        config_content = """
key1 = value1
key2= value2
key3 =value3
"""
        config_file.write_text(config_content.strip())

        config = TaskConfig.from_file(str(config_file))
        assert config.get("key1") == "value1"
        assert config.get("key2") == "value2"
        assert config.get("key3") == "value3"

    def test_parse_uda_definitions(self, temp_dir: Path) -> None:
        """Test parsing UDA definitions."""
        config_file = temp_dir / ".taskrc"
        config_content = """
uda.estimate.type=numeric
uda.estimate.label=Estimate
uda.estimate.values=
uda.complexity.type=string
uda.complexity.label=Complexity
uda.complexity.values=low,medium,high
"""
        config_file.write_text(config_content.strip())

        config = TaskConfig.from_file(str(config_file))
        udas = config.get_udas()

        assert "estimate" in udas
        assert udas["estimate"]["type"] == "numeric"
        assert udas["estimate"]["label"] == "Estimate"

        assert "complexity" in udas
        assert udas["complexity"]["type"] == "string"
        assert udas["complexity"]["values"] == "low,medium,high"

    def test_get_udas_with_no_udas(self, temp_dir: Path) -> None:
        """Test getting UDAs when none are defined."""
        config_file = temp_dir / ".taskrc"
        config_content = """
data.location=/home/user/.task
confirmation=off
"""
        config_file.write_text(config_content.strip())

        config = TaskConfig.from_file(str(config_file))
        udas = config.get_udas()
        assert udas == {}

    def test_get_value(self, temp_dir: Path) -> None:
        """Test getting specific config value."""
        config_file = temp_dir / ".taskrc"
        config_content = """
data.location=/home/user/.task
confirmation=off
"""
        config_file.write_text(config_content.strip())

        config = TaskConfig.from_file(str(config_file))
        assert config.get("data.location") == "/home/user/.task"
        assert config.get("confirmation") == "off"
        assert config.get("nonexistent") is None
        assert config.get("nonexistent", "default") == "default"

    def test_parse_color_config(self, temp_dir: Path) -> None:
        """Test parsing color configuration."""
        config_file = temp_dir / ".taskrc"
        config_content = """
color.active=rgb555 on rgb410
color.due=rgb550
color.overdue=rgb500
"""
        config_file.write_text(config_content.strip())

        config = TaskConfig.from_file(str(config_file))
        assert config.get("color.active") == "rgb555 on rgb410"
        assert config.get("color.due") == "rgb550"

    def test_parse_report_config(self, temp_dir: Path) -> None:
        """Test parsing report configuration."""
        config_file = temp_dir / ".taskrc"
        config_content = """
report.next.columns=id,start.age,entry.age,depends,priority,project,tags,recur,scheduled.countdown,due,until.remaining,description,urgency
report.next.labels=ID,Active,Age,Deps,P,Project,Tag,Recur,S,Due,Until,Description,Urg
report.next.filter=status:pending -WAITING
"""
        config_file.write_text(config_content.strip())

        config = TaskConfig.from_file(str(config_file))
        assert config.get("report.next.columns") is not None
        assert config.get("report.next.filter") == "status:pending -WAITING"

    def test_malformed_line_ignored(self, temp_dir: Path) -> None:
        """Test that malformed lines are ignored."""
        config_file = temp_dir / ".taskrc"
        config_content = """
data.location=/home/user/.task
this-line-has-no-equals
confirmation=off
"""
        config_file.write_text(config_content.strip())

        config = TaskConfig.from_file(str(config_file))
        assert len(config.options) == 2
        assert config.get("data.location") == "/home/user/.task"
        assert config.get("confirmation") == "off"
