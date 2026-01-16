#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "taskdantic",
#     "pyyaml",
# ]
# ///

# examples/advanced_config_example.py

"""Example using structured color and report configurations."""

from __future__ import annotations

from pathlib import Path
from tempfile import mkdtemp

import yaml

from taskdantic import TaskConfig


def create_advanced_yaml(yaml_path: Path) -> None:
    """Create advanced YAML configuration with structured models."""
    config = {
        "data": {"location": str(Path.home() / ".task")},
        "confirmation": False,
        # Structured color configurations
        "colors": {
            "active": {
                "foreground": "white",
                "background": "green",
            },
            "completed": {
                "foreground": "green",
                "background": "bright black",
            },
            "due": {
                "foreground": "red",
            },
            "overdue": {
                "foreground": "bold white",
                "background": "magenta",
            },
        },
        # Structured report configurations
        "reports": {
            "next": {
                "columns": "id,description,priority,due",
                "labels": "ID,Description,Priority,Due",
                "filter": "status:pending -WAITING",
                "sort": "urgency-",
                "description": "Next tasks to work on",
            },
            "inbox": {
                "columns": "id,description,tags",
                "labels": "ID,Description,Tags",
                "filter": "project:inbox status:pending",
                "sort": "urgency-",
            },
        },
        # Context definitions
        "contexts": {
            "work": {"filter": "+work"},
            "home": {"filter": "+home"},
        },
        # Default settings
        "defaults": {
            "command": "next",
            "project": "inbox",
        },
        # UDAs
        "udas": {
            "estimate": {
                "type": "numeric",
                "label": "Estimate (hours)",
            },
        },
    }

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)


def main() -> None:
    """Demonstrate advanced configuration features."""
    temp_dir = Path(mkdtemp(prefix="taskdantic_advanced_"))
    yaml_path = temp_dir / "taskdantic.yaml"
    taskrc_path = temp_dir / ".taskrc"

    print(f"Working directory: {temp_dir}\n")

    # Create advanced YAML config
    print("1. Creating advanced YAML configuration...")
    create_advanced_yaml(yaml_path)
    print(f"   Created: {yaml_path}")

    # Load and process
    print("\n2. Loading configuration...")
    config = TaskConfig.from_yaml(yaml_path)

    # Access colors
    print("\n3. Accessing color configurations:")
    colors = config.get_colors()
    for name, color_config in list(colors.items())[:3]:
        print(f"   {name}: {color_config.to_taskrc_value()}")

    # Access reports
    print("\n4. Accessing report configurations:")
    reports = config.get_reports()
    for name, report_config in reports.items():
        print(f"   {name}:")
        print(f"     - filter: {report_config.filter}")
        print(f"     - columns: {report_config.columns[:50]}...")

    # Write to .taskrc
    print("\n5. Writing to .taskrc format...")
    config.write_taskrc(taskrc_path)

    # Show sample output
    print("\n6. Sample .taskrc content:")
    print("   " + "-" * 60)
    with open(taskrc_path, encoding="utf-8") as f:
        lines = f.readlines()[:20]
        for line in lines:
            print(f"   {line.rstrip()}")
    print("   ...")
    print("   " + "-" * 60)

    print(f"\nFiles saved in: {temp_dir}")


if __name__ == "__main__":
    main()
