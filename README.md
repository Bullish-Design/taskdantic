# taskdantic

Pydantic models for the Taskwarrior JSON task format.

`taskdantic` provides a small, typed interface for creating Taskwarrior-compatible task objects in Python and
for parsing Taskwarrior's `task export` JSON back into validated models.

## What you get

- A `Task` model representing a Taskwarrior task (UUID, description, status, timestamps, tags, project, etc.).
- An `Annotation` model for Taskwarrior annotations.
- `Status` and `Priority` enums aligned with Taskwarrior values.
- Helpers that normalize common Taskwarrior JSON quirks:
  - Taskwarrior timestamps (`YYYYMMDDTHHmmssZ`) are parsed into timezone-aware `datetime` objects (UTC).
  - Task dependencies (`depends`) are accepted as either a single UUID string, a list of UUIDs/strings, or omitted,
    and are serialized to Taskwarrior’s comma-separated dependency string.

## Requirements

- Python >= 3.11
- Pydantic >= 2.0

## Install

```bash
pip install taskdantic
```

## Quickstart

### Create a task and export JSON for `task import`

```python
from datetime import datetime, timedelta

from taskdantic import Priority, Task

task = Task(
    description="Write documentation for Taskdantic",
    project="taskdantic",
    tags=["coding", "docs"],
    priority=Priority.HIGH,
    due=datetime.now() + timedelta(days=7),
)

# Dict suitable for JSON encoding and piping to `task import -`
payload = task.export_dict()

# Example:
#   echo '<json>' | task import -
```

### Parse Taskwarrior `task export` output

```python
import json
import subprocess

from taskdantic import Task

result = subprocess.run(["task", "export"], capture_output=True, text=True, check=True)
tasks_data = json.loads(result.stdout)

tasks = [Task.from_taskwarrior(item) for item in tasks_data]
print(tasks[0].description, tasks[0].status)
```

## Models

### Task

`Task` covers a practical subset of Taskwarrior’s task attributes:

- `uuid: UUID`
- `description: str`
- `status: Status` (default: `pending`)
- Timestamps: `entry`, `modified`, and optional `due`, `scheduled`, `start`, `end`, `wait`, `until`
- `project: str | None`
- `tags: list[str]`
- `priority: Priority | None`
- `annotations: list[Annotation]`
- `depends: list[UUID]`

The model is designed to work well with Taskwarrior’s JSON:

- Incoming Taskwarrior timestamps (e.g. `"20240115T143022Z"`) are parsed to `datetime` in UTC.
- When exporting (`export_dict()`), datetimes are serialized back to Taskwarrior timestamps.
- Dependencies serialize to the comma-separated string Taskwarrior expects (e.g. `"uuid1,uuid2"`).

### Annotation

An annotation includes:

- `entry: datetime` (Taskwarrior timestamp)
- `description: str`

## API

### `Task.export_dict(exclude_none: bool = True) -> dict[str, Any]`

Exports a JSON-ready dictionary intended for Taskwarrior import. By default, fields set to `None` are omitted.

### `Task.from_taskwarrior(data: dict[str, Any]) -> Task`

Parses one task object from `task export`. Taskwarrior export may include computed fields such as `id` and `urgency`;
these are ignored during parsing.

## Notes and limitations

- This library models Taskwarrior task JSON, not Taskwarrior configuration (`taskrc`).
- Taskwarrior has many attributes and behaviors; `taskdantic` focuses on a clean, validated core.
- Naive datetimes are treated as UTC during export.

## Development

```bash
pytest
```

Linting is configured via Ruff.

## License

See the repository for license information.
