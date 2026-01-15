# tests/test_config_writer.py

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from taskdantic.config_writer import TaskRcWriter, create_default_yaml


@pytest.mark.unit
class TestTaskRcWriter:
    """Test TaskRcWriter YAML to .taskrc conversion."""

    def test_load_yaml(self, temp_dir: Path) -> None:
        """Test loading YAML configuration."""
        yaml_file = temp_dir / "config.yaml"
        config = {"data": {"location": "/home/user/.task"}, "confirmation": False}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        writer = TaskRcWriter(yaml_file)
        loaded = writer.load_yaml()

        assert loaded["data"]["location"] == "/home/user/.task"
        assert loaded["confirmation"] is False

    def test_load_nonexistent_yaml(self, temp_dir: Path) -> None:
        """Test loading nonexistent YAML raises error."""
        yaml_file = temp_dir / "nonexistent.yaml"
        writer = TaskRcWriter(yaml_file)

        with pytest.raises(FileNotFoundError):
            writer.load_yaml()

    def test_write_simple_config(self, temp_dir: Path) -> None:
        """Test writing simple config to .taskrc."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        config = {"confirmation": False, "verbose": True}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        writer = TaskRcWriter(yaml_file)
        writer.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "confirmation=off" in content
        assert "verbose=on" in content

    def test_write_nested_config(self, temp_dir: Path) -> None:
        """Test writing nested config with dot notation."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        config = {"data": {"location": "/home/user/.task"}, "json": {"array": True}}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        writer = TaskRcWriter(yaml_file)
        writer.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "data.location=/home/user/.task" in content
        assert "json.array=on" in content

    def test_write_uda_definitions(self, temp_dir: Path) -> None:
        """Test writing UDA definitions."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        config = {
            "udas": {
                "estimate": {"type": "numeric", "label": "Estimate"},
                "complexity": {
                    "type": "string",
                    "label": "Complexity",
                    "values": ["low", "medium", "high"],
                },
            }
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        writer = TaskRcWriter(yaml_file)
        writer.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "uda.estimate.type=numeric" in content
        assert "uda.estimate.label=Estimate" in content
        assert "uda.complexity.type=string" in content
        assert "uda.complexity.values=low,medium,high" in content

    def test_write_list_values(self, temp_dir: Path) -> None:
        """Test writing list values as comma-separated."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        config = {"report": {"next": {"columns": ["id", "description", "priority"]}}}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        writer = TaskRcWriter(yaml_file)
        writer.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "report.next.columns=id,description,priority" in content

    def test_write_none_values(self, temp_dir: Path) -> None:
        """Test writing None values as empty."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        config = {"context": None}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        writer = TaskRcWriter(yaml_file)
        writer.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "context=" in content

    def test_write_boolean_values(self, temp_dir: Path) -> None:
        """Test boolean conversion to on/off."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        config = {"confirmation": False, "verbose": True, "hooks": False}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        writer = TaskRcWriter(yaml_file)
        writer.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "confirmation=off" in content
        assert "verbose=on" in content
        assert "hooks=off" in content

    def test_write_string_values(self, temp_dir: Path) -> None:
        """Test writing string values."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        config = {"color": {"active": "rgb555 on rgb410", "due": "rgb550"}}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        writer = TaskRcWriter(yaml_file)
        writer.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "color.active=rgb555 on rgb410" in content
        assert "color.due=rgb550" in content

    def test_write_numeric_values(self, temp_dir: Path) -> None:
        """Test writing numeric values."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        config = {"limits": {"max_tasks": 1000, "timeout": 30.5}}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        writer = TaskRcWriter(yaml_file)
        writer.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "limits.max_tasks=1000" in content
        assert "limits.timeout=30.5" in content

    def test_write_empty_config(self, temp_dir: Path) -> None:
        """Test writing empty config."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        config = {}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        writer = TaskRcWriter(yaml_file)
        writer.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        lines = [line for line in content.split("\n") if line and not line.startswith("#")]
        assert len(lines) == 0

    def test_write_deeply_nested_config(self, temp_dir: Path) -> None:
        """Test writing deeply nested configuration."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        config = {"report": {"next": {"columns": "id", "filter": "status:pending"}}}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        writer = TaskRcWriter(yaml_file)
        writer.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "report.next.columns=id" in content
        assert "report.next.filter=status:pending" in content

    def test_uda_without_values(self, temp_dir: Path) -> None:
        """Test UDA definition without values field."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        config = {"udas": {"estimate": {"type": "numeric", "label": "Hours"}}}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        writer = TaskRcWriter(yaml_file)
        writer.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "uda.estimate.type=numeric" in content
        assert "uda.estimate.label=Hours" in content
        assert "uda.estimate.values" not in content

    def test_uda_without_label(self, temp_dir: Path) -> None:
        """Test UDA definition without label field."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        config = {"udas": {"estimate": {"type": "numeric"}}}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        writer = TaskRcWriter(yaml_file)
        writer.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "uda.estimate.type=numeric" in content
        assert "uda.estimate.label" not in content


@pytest.mark.unit
class TestCreateDefaultYaml:
    """Test create_default_yaml function."""

    def test_create_default_yaml(self, temp_dir: Path) -> None:
        """Test creating default YAML config file."""
        yaml_file = temp_dir / "default.yaml"
        create_default_yaml(yaml_file)

        assert yaml_file.exists()

        with open(yaml_file, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        assert "data" in config
        assert "location" in config["data"]
        assert "confirmation" in config
        assert "json" in config
        assert "udas" in config

    def test_default_yaml_structure(self, temp_dir: Path) -> None:
        """Test default YAML has correct structure."""
        yaml_file = temp_dir / "default.yaml"
        create_default_yaml(yaml_file)

        with open(yaml_file, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        assert config["confirmation"] is False
        assert config["json"]["array"] is True
        assert config["hooks"] is False
        assert config["context"] is None
        assert isinstance(config["udas"], dict)

    def test_default_yaml_is_valid(self, temp_dir: Path) -> None:
        """Test default YAML can be loaded by TaskRcWriter."""
        yaml_file = temp_dir / "default.yaml"
        taskrc_file = temp_dir / ".taskrc"

        create_default_yaml(yaml_file)

        writer = TaskRcWriter(yaml_file)
        writer.write_taskrc(taskrc_file)

        assert taskrc_file.exists()
        content = taskrc_file.read_text()
        assert "confirmation=off" in content
