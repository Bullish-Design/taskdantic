# tests/test_config_yaml.py

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from taskdantic.config_models import TaskConfig, UDADefinition


@pytest.mark.unit
class TestTaskConfigFromYaml:
    """Test TaskConfig.from_yaml() loading."""

    def test_load_nonexistent_file(self, temp_dir: Path) -> None:
        """Test loading nonexistent file returns empty config."""
        yaml_file = temp_dir / "nonexistent.yaml"
        config = TaskConfig.from_yaml(yaml_file)

        assert config.config == {}
        assert config.udas == {}
        assert config.data_location is None

    def test_load_empty_file(self, temp_dir: Path) -> None:
        """Test loading empty YAML file."""
        yaml_file = temp_dir / "empty.yaml"
        yaml_file.write_text("")

        config = TaskConfig.from_yaml(yaml_file)

        assert config.config == {}
        assert config.udas == {}

    def test_load_simple_config(self, temp_dir: Path) -> None:
        """Test loading simple configuration."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {
            "confirmation": False,
            "verbose": True,
            "hooks": False,
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert config.config["confirmation"] is False
        assert config.config["verbose"] is True
        assert config.config["hooks"] is False

    def test_load_data_location(self, temp_dir: Path) -> None:
        """Test extracting data.location field."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {"data": {"location": "/home/user/.task"}}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert config.data_location == "/home/user/.task"
        assert "data" in config.config

    def test_load_nested_config(self, temp_dir: Path) -> None:
        """Test loading nested configuration."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {
            "data": {"location": "/home/user/.task"},
            "json": {"array": True, "depends": {"array": False}},
            "color": {"active": "rgb555", "due": "rgb550"},
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert config.get("data.location") == "/home/user/.task"
        assert config.get("json.array") is True
        assert config.get("color.active") == "rgb555"

    def test_load_structured_colors(self, temp_dir: Path) -> None:
        """Test loading structured color configurations."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {
            "colors": {
                "active": {"foreground": "white", "background": "green"},
                "due": {"foreground": "red"},
            }
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert "colors" in config.config
        assert config.config["colors"]["active"]["foreground"] == "white"
        assert config.config["colors"]["active"]["background"] == "green"

    def test_load_structured_reports(self, temp_dir: Path) -> None:
        """Test loading structured report configurations."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {
            "reports": {
                "next": {
                    "columns": "id,description",
                    "labels": "ID,Description",
                    "filter": "status:pending",
                    "sort": "urgency-",
                }
            }
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert "reports" in config.config
        assert config.config["reports"]["next"]["columns"] == "id,description"
        assert config.config["reports"]["next"]["filter"] == "status:pending"

    def test_load_contexts(self, temp_dir: Path) -> None:
        """Test loading context configurations."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {
            "contexts": {
                "work": {"filter": "+work"},
                "home": "+home",
            }
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert "contexts" in config.config
        assert config.config["contexts"]["work"]["filter"] == "+work"

    def test_load_defaults(self, temp_dir: Path) -> None:
        """Test loading default settings."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {
            "defaults": {
                "command": "next",
                "project": "inbox",
            }
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert "defaults" in config.config
        assert config.config["defaults"]["command"] == "next"

    def test_load_udas(self, temp_dir: Path) -> None:
        """Test loading UDA definitions."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {
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
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert "estimate" in config.udas
        assert isinstance(config.udas["estimate"], UDADefinition)
        assert config.udas["estimate"].type == "numeric"
        assert config.udas["estimate"].label == "Estimate"

        assert "complexity" in config.udas
        assert config.udas["complexity"].type == "string"
        assert config.udas["complexity"].values == ["low", "medium", "high"]

    def test_load_complete_config(self, temp_dir: Path) -> None:
        """Test loading complete configuration with all features."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {
            "data": {"location": "/home/user/.task"},
            "confirmation": False,
            "colors": {
                "active": {"foreground": "white", "background": "green"},
            },
            "reports": {
                "next": {
                    "columns": "id,description",
                    "labels": "ID,Description",
                    "filter": "status:pending",
                }
            },
            "contexts": {"work": {"filter": "+work"}},
            "defaults": {"command": "next"},
            "udas": {
                "estimate": {"type": "numeric", "label": "Estimate"},
            },
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert config.data_location == "/home/user/.task"
        assert len(config.udas) == 1
        assert config.get("confirmation") is False
        assert "colors" in config.config
        assert "reports" in config.config

    def test_get_with_default(self, temp_dir: Path) -> None:
        """Test get() method with default values."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {"confirmation": False}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert config.get("confirmation") is False
        assert config.get("nonexistent") is None
        assert config.get("nonexistent", "default") == "default"

    def test_get_nested_with_default(self, temp_dir: Path) -> None:
        """Test get() for nested keys with defaults."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {"data": {"location": "/home/user/.task"}}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert config.get("data.location") == "/home/user/.task"
        assert config.get("data.nonexistent") is None
        assert config.get("nonexistent.key") is None
        assert config.get("nonexistent.key", "default") == "default"

    def test_get_udas_method(self, temp_dir: Path) -> None:
        """Test get_udas() method returns correct format."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {
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
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)
        udas = config.get_udas()

        assert "estimate" in udas
        assert udas["estimate"]["type"] == "numeric"
        assert udas["estimate"]["label"] == "Estimate"

        assert "complexity" in udas
        assert udas["complexity"]["type"] == "string"
        assert udas["complexity"]["values"] == "low,medium,high"


@pytest.mark.unit
class TestTaskConfigWriteTaskrc:
    """Test TaskConfig.write_taskrc() method."""

    def test_write_simple_taskrc(self, temp_dir: Path) -> None:
        """Test writing simple config to .taskrc."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        yaml_content = {"confirmation": False, "verbose": True}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)
        config.write_taskrc(taskrc_file)

        assert taskrc_file.exists()
        content = taskrc_file.read_text()
        assert "confirmation=off" in content
        assert "verbose=on" in content

    def test_write_with_data_location(self, temp_dir: Path) -> None:
        """Test writing config with data.location."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        yaml_content = {"data": {"location": "/home/user/.task"}}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)
        config.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "data.location=/home/user/.task" in content

    def test_write_with_structured_colors(self, temp_dir: Path) -> None:
        """Test writing structured colors to .taskrc."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        yaml_content = {
            "colors": {
                "active": {"foreground": "white", "background": "green"},
                "due": {"foreground": "red"},
            }
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)
        config.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "color.active=white on green" in content
        assert "color.due=red" in content

    def test_write_with_structured_reports(self, temp_dir: Path) -> None:
        """Test writing structured reports to .taskrc."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        yaml_content = {
            "reports": {
                "next": {
                    "columns": "id,description",
                    "labels": "ID,Description",
                    "filter": "status:pending",
                }
            }
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)
        config.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "report.next.columns=id,description" in content
        assert "report.next.labels=ID,Description" in content
        assert "report.next.filter=status:pending" in content

    def test_write_with_udas(self, temp_dir: Path) -> None:
        """Test writing config with UDA definitions."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        yaml_content = {
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
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)
        config.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "uda.estimate.type=numeric" in content
        assert "uda.estimate.label=Estimate" in content
        assert "uda.complexity.values=low,medium,high" in content

    def test_write_complete_config(self, temp_dir: Path) -> None:
        """Test writing complete configuration."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        yaml_content = {
            "data": {"location": "/home/user/.task"},
            "confirmation": False,
            "colors": {"active": {"foreground": "white", "background": "green"}},
            "reports": {
                "next": {
                    "columns": "id,description",
                    "labels": "ID,Description",
                    "filter": "status:pending",
                }
            },
            "contexts": {"work": {"filter": "+work"}},
            "defaults": {"command": "next"},
            "udas": {"estimate": {"type": "numeric"}},
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)
        config.write_taskrc(taskrc_file)

        content = taskrc_file.read_text()
        assert "data.location=/home/user/.task" in content
        assert "confirmation=off" in content
        assert "color.active=white on green" in content
        assert "report.next.columns=id,description" in content
        assert "context.work=+work" in content
        assert "default.command=next" in content
        assert "uda.estimate.type=numeric" in content

    def test_roundtrip_yaml_to_taskrc(self, temp_dir: Path) -> None:
        """Test YAML → TaskConfig → .taskrc roundtrip."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        yaml_content = {
            "data": {"location": "/home/user/.task"},
            "confirmation": False,
            "udas": {
                "estimate": {"type": "numeric", "label": "Hours"},
            },
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)
        config.write_taskrc(taskrc_file)

        assert config.data_location == "/home/user/.task"
        assert "estimate" in config.udas

        content = taskrc_file.read_text()
        assert "data.location=/home/user/.task" in content
        assert "confirmation=off" in content
        assert "uda.estimate.type=numeric" in content

    def test_write_empty_config(self, temp_dir: Path) -> None:
        """Test writing empty config."""
        yaml_file = temp_dir / "config.yaml"
        taskrc_file = temp_dir / ".taskrc"

        yaml_content = {}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)
        config.write_taskrc(taskrc_file)

        assert taskrc_file.exists()


@pytest.mark.unit
class TestTaskConfigEdgeCases:
    """Test edge cases for TaskConfig YAML handling."""

    def test_yaml_with_comments(self, temp_dir: Path) -> None:
        """Test YAML with comments loads correctly."""
        yaml_file = temp_dir / "config.yaml"

        yaml_text = """
# This is a comment
confirmation: false
# Another comment
verbose: true
"""
        yaml_file.write_text(yaml_text)

        config = TaskConfig.from_yaml(yaml_file)

        assert config.config["confirmation"] is False
        assert config.config["verbose"] is True

    def test_yaml_with_special_characters(self, temp_dir: Path) -> None:
        """Test YAML with special characters in values."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {
            "color": {"active": "rgb555 on rgb410", "due": "bold red"},
            "report": {"next": {"filter": "status:pending -WAITING"}},
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert config.get("color.active") == "rgb555 on rgb410"
        assert config.get("report.next.filter") == "status:pending -WAITING"

    def test_yaml_with_numeric_keys(self, temp_dir: Path) -> None:
        """Test YAML with numeric values."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {"limits": {"max_tasks": 1000, "timeout": 30}}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert config.get("limits.max_tasks") == 1000
        assert config.get("limits.timeout") == 30

    def test_uda_with_minimal_fields(self, temp_dir: Path) -> None:
        """Test UDA with only type field."""
        yaml_file = temp_dir / "config.yaml"
        yaml_content = {"udas": {"estimate": {"type": "numeric"}}}

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_content, f)

        config = TaskConfig.from_yaml(yaml_file)

        assert "estimate" in config.udas
        assert config.udas["estimate"].type == "numeric"
        assert config.udas["estimate"].label is None
        assert config.udas["estimate"].values is None
