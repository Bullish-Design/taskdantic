#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "taskdantic",
#     "pyyaml",
# ]
# ///

# examples/yaml_config_example.py

"""Example: Using YAML configuration with Taskdantic."""

from __future__ import annotations

from pathlib import Path
from tempfile import mkdtemp

import yaml

from taskdantic import TaskConfig, TaskWarrior


def create_example_yaml(yaml_path: Path) -> None:
    """Create example YAML configuration."""
    config = {
        "data": {"location": str(Path.home() / ".task")},
        "confirmation": False,
        "json": {"array": True},
        "hooks": False,
        "udas": {
            "estimate": {
                "type": "numeric",
                "label": "Estimate (hours)",
            },
            "complexity": {
                "type": "string",
                "label": "Complexity",
                "values": ["low", "medium", "high"],
            },
        },
        "color": {
            "active": "rgb555 on rgb410",
            "due": "rgb550",
        },
    }

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)


def main() -> None:
    """Demonstrate YAML config workflow."""
    # Create temporary directory for demo
    temp_dir = Path(mkdtemp(prefix="taskdantic_yaml_demo_"))
    yaml_path = temp_dir / "taskdantic.yaml"
    taskrc_path = temp_dir / ".taskrc"

    print(f"Demo directory: {temp_dir}\n")

    # Step 1: Create YAML config
    print("1. Creating YAML configuration...")
    create_example_yaml(yaml_path)
    print(f"   Created: {yaml_path}")

    # Step 2: Load YAML into TaskConfig
    print("\n2. Loading YAML configuration...")
    config = TaskConfig.from_yaml(yaml_path)
    print(f"   Data location: {config.data_location}")
    print(f"   UDAs defined: {list(config.get_udas().keys())}")

    # Step 3: Write to .taskrc format
    print("\n3. Writing to .taskrc format...")
    config.write_taskrc(taskrc_path)
    print(f"   Written to: {taskrc_path}")

    # Step 4: Show .taskrc content
    print("\n4. Generated .taskrc content:")
    print("   " + "-" * 60)
    with open(taskrc_path, encoding="utf-8") as f:
        for line in f:
            print(f"   {line.rstrip()}")
    print("   " + "-" * 60)

    # Step 5: Use with TaskWarrior
    print("\n5. Using with TaskWarrior...")
    tw = TaskWarrior(config_filename=str(taskrc_path))
    print(f"   TaskWarrior version: {tw.get_version()}")
    print(f"   UDAs available: {list(tw.load_config().get_udas().keys())}")

    print(f"\nDemo files saved in: {temp_dir}")
    print("You can inspect the files or delete the directory when done.")


if __name__ == "__main__":
    main()
