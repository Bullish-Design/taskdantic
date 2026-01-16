# README_UDA_INHERITANCE.md

## User Defined Attributes (UDAs)

Taskdantic supports Taskwarrior's User Defined Attributes through Task inheritance. Define your UDAs as Pydantic fields on Task subclasses for full type safety and validation.

### Quick Start

```python
from datetime import timedelta
from pydantic import field_validator
from taskdantic import Task, Priority

class AgileTask(Task):
    """Task with Agile UDAs."""
    sprint: str | None = None
    points: int = 0
    estimate: timedelta | None = None
    
    @field_validator("sprint")
    @classmethod
    def validate_sprint(cls, v: str | None) -> str | None:
        if v and not v.startswith("Sprint "):
            return f"Sprint {v}"
        return v

# Use with full type safety and IDE support
task = AgileTask(
    description="Implement OAuth2",
    priority=Priority.HIGH,
    sprint="23",  # Auto-prefixed to "Sprint 23"
    points=8,
    estimate=timedelta(hours=6)
)
```

### Benefits

- **Full Pydantic features**: Type hints, Field() constraints, validators, defaults
- **IDE support**: Autocomplete and type checking work perfectly
- **Type safety**: Automatic type coercion and validation
- **Natural syntax**: UDAs are first-class fields, not in a separate namespace

### Supported UDA Types

UDA fields automatically handle Taskwarrior-specific formats:

**Datetime** - Parses Taskwarrior timestamps:
```python
class MyTask(Task):
    reviewed: datetime | None = None

task = MyTask(description="Test", reviewed="20240120T100000Z")
# Parsed to datetime(2024, 1, 20, 10, 0, 0, tzinfo=timezone.utc)
```

**Timedelta** - Parses ISO 8601 durations:
```python
class MyTask(Task):
    estimate: timedelta | None = None

task = MyTask(description="Test", estimate="PT2H30M")
# Parsed to timedelta(hours=2, minutes=30)
```

**UUID Lists** - Parses comma-separated strings:
```python
from uuid import UUID

class MyTask(Task):
    blocked_by: list[UUID] | None = None

task = MyTask(description="Test", blocked_by="uuid1,uuid2")
# Parsed to [UUID("uuid1"), UUID("uuid2")]
```

### Validation

Use Pydantic features for validation:

```python
from pydantic import Field, field_validator

class ValidatedTask(Task):
    points: int = Field(ge=0, le=100, description="Story points")
    severity: str = Field(pattern="^(low|medium|high|critical)$")
    
    @field_validator("points")
    @classmethod
    def validate_points(cls, v: int) -> int:
        if v % 2 != 0:
            raise ValueError("Points must be even")
        return v
```

### Multiple Task Types

Define different task types for different purposes:

```python
class AgileTask(Task):
    sprint: str | None = None
    points: int = 0

class BugTask(Task):
    severity: str = "medium"
    reported_by: str | None = None

class DevOpsTask(Task):
    environment: str | None = None
    rollback_safe: bool = True

# Use appropriate type for each task
feature = AgileTask(description="Feature", sprint="Sprint 23", points=8)
bug = BugTask(description="Bug", severity="high")
deploy = DevOpsTask(description="Deploy", environment="prod")
```

### Export/Import

UDAs are seamlessly preserved through export/import:

```python
task = AgileTask(
    description="Test",
    sprint="Sprint 25",
    points=8,
    estimate=timedelta(hours=4)
)

# Export to Taskwarrior format
exported = task.export_dict()
# {
#   "uuid": "...",
#   "description": "Test",
#   "sprint": "Sprint 25",
#   "points": 8,
#   "estimate": "PT4H",
#   ...
# }

# Import back
imported = AgileTask.from_taskwarrior(exported)
assert imported.sprint == "Sprint 25"
assert imported.points == 8
```

### Taskwarrior Compatibility

Tasks import cleanly from Taskwarrior, ignoring computed fields:

```python
# Data from 'task export'
tw_data = {
    "id": 42,              # Ignored
    "urgency": 10.5,       # Ignored
    "uuid": "...",
    "description": "Task",
    "sprint": "Sprint 28",  # Your UDA
    "points": 5             # Your UDA
}

task = AgileTask.from_taskwarrior(tw_data)
# Only core fields and your UDAs are imported
```

### Inheritance Patterns

UDAs support inheritance for shared fields:

```python
class TrackedTask(Task):
    """Base task with time tracking."""
    time_spent: timedelta | None = None

class TrackedAgileTask(TrackedTask):
    """Agile task with time tracking."""
    sprint: str | None = None
    points: int = 0

task = TrackedAgileTask(
    description="Feature",
    sprint="Sprint 30",
    points=5,
    time_spent=timedelta(hours=4)
)
```

### Default Values

Use Pydantic defaults:

```python
class TaskWithDefaults(Task):
    priority_score: float = 1.0
    complexity: int = Field(default=1)
    auto_close: bool = False
```

### Working with Collections

Type-specific operations work naturally:

```python
tasks: list[AgileTask] = [
    AgileTask(description="Task A", sprint="Sprint 27", points=8),
    AgileTask(description="Task B", sprint="Sprint 27", points=5),
]

# Calculate sprint totals
total_points = sum(t.points for t in tasks)

# Group by sprint
by_sprint = {}
for task in tasks:
    if task.sprint not in by_sprint:
        by_sprint[task.sprint] = []
    by_sprint[task.sprint].append(task)
```

### Unknown UDAs

Unknown UDAs from imports are preserved:

```python
data = {
    "description": "Test",
    "sprint": "Sprint 23",      # Known UDA
    "custom_field": "value"     # Unknown UDA
}

task = AgileTask.from_taskwarrior(data)
task.sprint              # Works: "Sprint 23"
task.custom_field        # Works: "value" (stored in __pydantic_extra__)
```

### Migration from Base Task

If you have existing code using base `Task`, you can create a subclass with your UDAs and gradually migrate:

```python
# Old code
task = Task(description="Test")

# New code with UDAs
task = AgileTask(description="Test", sprint="Sprint 23", points=8)

# Both export to compatible Taskwarrior JSON
```
