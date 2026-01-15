# taskdantic

Modern Pydantic-based Python library for Taskwarrior, providing type-safe task management through the `task` CLI.

## Features

- **Pydantic Models**: Full type safety and validation for tasks
- **Clean API**: Intuitive interface for CRUD operations
- **Type Hints**: Complete type coverage for IDE support
- **Datetime Handling**: Automatic parsing and serialization of Taskwarrior date formats
- **UDA Support**: User-Defined Attributes via Pydantic's `model_extra`
- **Config Parsing**: Read and parse `.taskrc` files

## Installation

Using UV:
```bash
uv pip install taskdantic
```

## Quick Start

```python
from taskdantic import TaskWarrior, TaskStatus, Priority

# Initialize
tw = TaskWarrior()

# Add a task
task = tw.add("Write documentation", project="taskdantic", priority=Priority.HIGH)
print(f"Created task {task.uuid}")

# Get a task
task = tw.get(uuid=task.uuid)
print(task.description)

# Update task
task.priority = Priority.MEDIUM
task = tw.update(task)

# Complete task
task = tw.complete(uuid=task.uuid)

# Load all pending tasks
pending = tw.load_tasks(status=TaskStatus.PENDING)
for task in pending:
    print(f"- {task.description}")
```

## Advanced Usage

### Custom Config

```python
tw = TaskWarrior(
    config_filename="~/projects/.taskrc",
    config_overrides={"verbose": "no"}
)
```

### Filtering

```python
# Simple filter
tasks = tw.filter_tasks("project:work")

# Complex filter
tasks = tw.filter_tasks("project:work status:pending priority:H")

# Filter by status
tasks = tw.load_tasks(status=[TaskStatus.PENDING, TaskStatus.WAITING])
```

### Working with UDAs

```python
# Task with UDA (assuming 'estimate' is defined in .taskrc)
task = tw.add(
    "Review PR",
    project="dev",
    estimate=2,  # UDA field
)

# Access UDA via model_extra
print(task.model_extra.get("estimate"))
```

### Annotations

```python
# Add annotation
task = tw.annotate(task.uuid, "This is important")

# Remove annotation
task = tw.denotate(task.uuid, "This is important")
```

### Task Lifecycle

```python
# Start a task
task = tw.start(uuid=task.uuid)

# Stop a task
task = tw.stop(uuid=task.uuid)

# Delete a task
task = tw.delete(uuid=task.uuid)
```

## Models

### Task

Core fields:
- `uuid`: Unique identifier
- `description`: Task description
- `status`: TaskStatus enum (pending, completed, deleted, waiting, recurring)
- `project`: Project name
- `tags`: List of tags
- `priority`: Priority enum (H, M, L)

Date fields:
- `entry`, `modified`, `start`, `end`, `due`, `until`, `wait`, `scheduled`

Dependencies:
- `depends`: List of UUID dependencies
- `parent`: Parent task UUID

Recurrence:
- `recur`: Recurrence interval (timedelta)
- `mask`, `imask`: Recurrence masks

### TaskStatus

```python
class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    DELETED = "deleted"
    WAITING = "waiting"
    RECURRING = "recurring"
```

### Priority

```python
class Priority(str, Enum):
    HIGH = "H"
    MEDIUM = "M"
    LOW = "L"
```

## Requirements

- Python 3.11+
- Taskwarrior 2.6+
- Pydantic 2.0+

## Development

```bash
# Setup
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/taskdantic

# Linting
ruff check src/taskdantic
```

## Differences from Original taskw

1. **Pydantic Models**: Tasks are Pydantic models instead of plain dicts
2. **Type Safety**: Full type hints and validation
3. **Datetime Objects**: Dates are always datetime objects, not strings
4. **UDAs**: Accessed via `model_extra` instead of separate `udas` dict
5. **Cleaner API**: More intuitive method names and arguments

## License

MIT License
