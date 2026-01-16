# README_UDA.md

## User Defined Attributes (UDAs)

Taskdantic supports Taskwarrior's User Defined Attributes through Task inheritance with custom field types for automatic format handling.

### Quick Start

```python
from taskdantic import Task, TWDatetime, TWDuration, Priority
from pydantic import field_validator

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
    sprint="23",              # Auto-prefixed to "Sprint 23"
    points=8,
    estimate="PT6H",          # ISO 8601 → timedelta
    reviewed="20240120T100000Z"  # Taskwarrior → datetime
)
```

### Custom Field Types

**TWDatetime** - Datetime with Taskwarrior timestamp support
```python
from taskdantic import TWDatetime

class MyTask(Task):
    reviewed: TWDatetime | None = None

task = MyTask(description="Test", reviewed="20240120T100000Z")
# Automatically parsed to datetime(2024, 1, 20, 10, 0, 0, tzinfo=UTC)

exported = task.export_dict()
# Automatically serialized to "20240120T100000Z"
```

**TWDuration** - Timedelta with ISO 8601 duration support
```python
from taskdantic import TWDuration

class MyTask(Task):
    estimate: TWDuration | None = None

task = MyTask(description="Test", estimate="PT2H30M")
# Automatically parsed to timedelta(hours=2, minutes=30)

exported = task.export_dict()
# Automatically serialized to "PT2H30M"
```

**UUIDList** - List of UUIDs with comma-separated string support
```python
from taskdantic import UUIDList
from uuid import UUID

class MyTask(Task):
    blocked_by: UUIDList | None = None

task = MyTask(description="Test", blocked_by="uuid1,uuid2")
# Automatically parsed to [UUID("uuid1"), UUID("uuid2")]

exported = task.export_dict()
# Automatically serialized to "uuid1,uuid2"
```

### Validation

Use full Pydantic validation features:

```python
from pydantic import Field, field_validator

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

### Multiple Task Types

```python
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

feature = AgileTask(description="Feature", sprint="Sprint 23", points=8)
bug = BugTask(description="Bug", severity="high")
deploy = DevOpsTask(description="Deploy", environment="prod")
```

### Export/Import

UDAs automatically serialize/deserialize:

```python
task = AgileTask(
    description="Test",
    sprint="Sprint 25",
    points=8,
    estimate=timedelta(hours=4),
    reviewed=datetime(2024, 1, 20, 10, 0, 0, tzinfo=timezone.utc)
)

# Export
exported = task.export_dict()
# {
#   "sprint": "Sprint 25",
#   "points": 8,
#   "estimate": "PT4H",
#   "reviewed": "20240120T100000Z",
#   ...
# }

# Import
imported = AgileTask.from_taskwarrior(exported)
assert imported.sprint == "Sprint 25"
assert imported.estimate == timedelta(hours=4)
```

### Taskwarrior Compatibility

Computed fields automatically ignored:

```python
tw_data = {
    "id": 42,              # Ignored
    "urgency": 10.5,       # Ignored
    "description": "Task",
    "sprint": "Sprint 28",
    "points": 5
}

task = AgileTask.from_taskwarrior(tw_data)
# Only core fields and UDAs imported
```

### Inheritance

```python
class BaseTask(Task):
    time_spent: TWDuration | None = None

class TrackedAgileTask(BaseTask):
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

```python
class TaskWithDefaults(Task):
    priority_score: float = 1.0
    complexity: int = Field(default=1)
    auto_close: bool = False
```

### Working with Collections

```python
tasks = [
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

Unknown fields stored in `__pydantic_extra__`:

```python
data = {
    "description": "Test",
    "sprint": "Sprint 23",      # Known UDA
    "custom_field": "value"     # Unknown UDA
}

task = AgileTask.from_taskwarrior(data)
task.sprint  # "Sprint 23"
task.__pydantic_extra__["custom_field"]  # "value"
```

### API Reference

**Custom Types:**
- `TWDatetime` - Datetime with Taskwarrior timestamp format
- `TWDuration` - Timedelta with ISO 8601 duration format
- `UUIDList` - List of UUIDs with comma-separated format

**Task Methods:**
- `export_dict(exclude_none=True)` - Export to Taskwarrior JSON
- `from_taskwarrior(data)` - Import from Taskwarrior JSON

### Type Compatibility

Custom types are subclasses of standard Python types:

```python
isinstance(TWDatetime.now(), datetime)  # True
isinstance(TWDuration(hours=2), timedelta)  # True
isinstance(UUIDList([UUID(...)]), list)  # True
```

This means you can use them with any code expecting standard types.
