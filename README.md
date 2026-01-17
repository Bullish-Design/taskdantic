# taskdantic

Pydantic models for the Taskwarrior JSON task format.

`taskdantic` provides a small, typed interface for creating Taskwarrior-compatible task objects in Python and
for parsing Taskwarrior's `task export` JSON back into validated models.

It also supports Taskwarrior **User Defined Attributes (UDAs)** via normal Pydantic inheritance: define UDAs as
fields on `Task` subclasses, optionally using the provided custom field types to automatically handle Taskwarrior
formats (timestamps, durations, comma-separated UUID lists).

## What you get

- A `Task` model representing a Taskwarrior task (UUID, description, status, timestamps, tags, project, etc.).
- An `Annotation` model for Taskwarrior annotations.
- `Status` and `Priority` enums aligned with Taskwarrior values.
- Helpers that normalize common Taskwarrior JSON quirks:
  - Taskwarrior timestamps (`YYYYMMDDTHHmmssZ`) are parsed into timezone-aware `datetime` objects (UTC).
  - Task dependencies (`depends`) are accepted as either a comma-separated UUID string, a list of UUIDs/strings, or omitted,
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
payload = task.to_taskwarrior()
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
- When exporting (`to_taskwarrior()`), datetimes are serialized back to Taskwarrior timestamps.
- Dependencies serialize to the comma-separated string Taskwarrior expects (e.g. `"uuid1,uuid2"`).

### Annotation

An annotation includes:

- `entry: TWDatetime` (Taskwarrior timestamp)
- `description: str`

## User Defined Attributes (UDAs)

Taskdantic supports Taskwarrior's UDAs through normal Python inheritance: define your UDAs as Pydantic fields
on a `Task` subclass for type safety, validation, defaults, and IDE support.

For Taskwarrior-specific formats, use the custom field types:

- `TWDatetime` for Taskwarrior timestamps (`YYYYMMDDTHHmmssZ`)
- `TWDuration` for ISO 8601 durations (`PT#H#M#S`)
- `UUIDList` for comma-separated UUID lists (`uuid1,uuid2`)

### Quick start

```python
from pydantic import field_validator

from taskdantic import Priority, Task, TWDatetime, TWDuration


class AgileTask(Task):
    sprint: str | None = None
    points: int = 0
    estimate: TWDuration | None = None
    reviewed: TWDatetime | None = None

    @field_validator("sprint")
    @classmethod
    def validate_sprint(cls, v):
        if v and not v.startswith("Sprint "):
            return f"Sprint {v}"
        return v


task = AgileTask(
    description="Implement OAuth2",
    priority=Priority.HIGH,
    sprint="23",                 # Auto-prefixed to "Sprint 23"
    points=8,
    estimate="PT6H",             # ISO 8601 -> timedelta
    reviewed="20240120T100000Z", # Taskwarrior -> datetime
)
```

### Custom field types

#### TWDatetime (Taskwarrior timestamps)

```python
from taskdantic import TWDatetime, Task


class MyTask(Task):
    reviewed: TWDatetime | None = None


task = MyTask(description="Test", reviewed="20240120T100000Z")
exported = task.to_taskwarrior()
# reviewed -> "20240120T100000Z"
```

#### TWDuration (ISO 8601 durations)

```python
from taskdantic import TWDuration, Task


class MyTask(Task):
    estimate: TWDuration | None = None


task = MyTask(description="Test", estimate="PT2H30M")
exported = task.to_taskwarrior()
# estimate -> "PT2H30M"
```

#### UUIDList (comma-separated UUID lists)

```python
from taskdantic import UUIDList, Task


class MyTask(Task):
    blocked_by: UUIDList | None = None


task = MyTask(description="Test", blocked_by="uuid1,uuid2")
exported = task.to_taskwarrior()
# blocked_by -> "uuid1,uuid2"
```

### Validation

UDAs work with all Pydantic validation features:

```python
from datetime import timedelta

from pydantic import Field, field_validator

from taskdantic import Task, TWDuration


class ValidatedTask(Task):
    points: int = Field(ge=0, le=100, description="Story points")
    severity: str = Field(pattern="^(low|medium|high|critical)$")
    estimate: TWDuration | None = None

    @field_validator("points")
    @classmethod
    def validate_points(cls, v):
        if v % 2 != 0:
            raise ValueError("Points must be even")
        return v

    @field_validator("estimate")
    @classmethod
    def validate_estimate(cls, v):
        if v and v > timedelta(days=30):
            raise ValueError("Estimate too long")
        return v
```

### Multiple task types

```python
from taskdantic import Task, TWDatetime, TWDuration


class AgileTask(Task):
    sprint: str | None = None
    points: int = 0
    estimate: TWDuration | None = None


class BugTask(Task):
    severity: str = "medium"
    reported_by: str | None = None
    fixed_in: str | None = None


class DevOpsTask(Task):
    environment: str | None = None
    deployment_time: TWDatetime | None = None
    rollback_safe: bool = True
```

### Export/Import (UDAs)

UDAs automatically serialize/deserialize when you use the custom field types:

```python
from datetime import datetime, timedelta, timezone

from taskdantic import Task, TWDatetime, TWDuration


class AgileTask(Task):
    sprint: str | None = None
    points: int = 0
    estimate: TWDuration | None = None
    reviewed: TWDatetime | None = None


task = AgileTask(
    description="Test",
    sprint="Sprint 25",
    points=8,
    estimate=timedelta(hours=4),
    reviewed=datetime(2024, 1, 20, 10, 0, 0, tzinfo=timezone.utc),
)

exported = task.to_taskwarrior()
imported = AgileTask.from_taskwarrior(exported)

assert imported.sprint == "Sprint 25"
assert imported.estimate == timedelta(hours=4)
```

### Inheritance patterns

```python
from taskdantic import Task, TWDuration


class TrackedTask(Task):
    time_spent: TWDuration | None = None


class TrackedAgileTask(TrackedTask):
    sprint: str | None = None
    points: int = 0
```

### Unknown UDAs

Unknown fields coming from Taskwarrior exports are preserved via Pydantic extra fields:

```python
data = {
    "description": "Test",
    "sprint": "Sprint 23",      # Known UDA
    "custom_field": "value"     # Unknown UDA
}


class AgileTask(Task):
    sprint: str | None = None


task = AgileTask.from_taskwarrior(data)

```

## API

### `Task.to_taskwarrior(exclude_none: bool = True) -> dict[str, Any]`

Exports a JSON-ready dictionary intended for Taskwarrior import. By default, fields set to `None` are omitted.

### `Task.from_taskwarrior(data: dict[str, Any]) -> Task`

Parses one task object from `task export`. Taskwarrior export may include computed fields such as `id` and `urgency`;
these are ignored during parsing.

## Notes and limitations

- This library models Taskwarrior task JSON, not Taskwarrior configuration (`taskrc`).
- Taskwarrior has many attributes and behaviors; `taskdantic` focuses on a clean, validated core.
- Naive datetimes are treated as UTC during export.

## Type compatibility

Custom types are subclasses of standard Python types:

```python
from datetime import datetime, timedelta

from taskdantic import TWDatetime, TWDuration, UUIDList

assert isinstance(TWDatetime.now(), datetime)
assert isinstance(TWDuration(hours=2), timedelta)
assert isinstance(UUIDList([]), list)
```
