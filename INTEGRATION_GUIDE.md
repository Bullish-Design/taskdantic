# INTEGRATION_GUIDE.md

## UDA Custom Types Implementation - Integration Guide

### Files to Replace

1. **src/taskdantic/models.py**
   - Replace with: `models_final.py`
   - Changes: Simplified, removed UDA-specific parsing logic (now handled by custom types)

2. **src/taskdantic/__init__.py**
   - Replace with: `__init__.py`
   - Changes: Added exports for TWDatetime, TWDuration, UUIDList

3. **tests/test_uda_inheritance.py**
   - Replace with: `test_uda_inheritance_final.py`
   - Changes: Updated to use custom types

4. **tests/test_uda_integration.py**
   - Replace with: `test_uda_integration_final.py`
   - Changes: Updated to use custom types

5. **examples/basic_usage.py**
   - Replace with: `basic_usage_final.py`
   - Changes: Updated to use custom types

6. **examples/uda_usage.py** (if exists, or create new)
   - Use: `uda_usage_final.py`
   - Changes: Comprehensive example with custom types

### New Files to Add

1. **src/taskdantic/types.py**
   - Use: `types.py`
   - Purpose: Custom Pydantic types for UDA fields

2. **README_UDA.md** (or append to existing README.md)
   - Use: `README_UDA_FINAL.md`
   - Purpose: Documentation for UDA functionality

### Key Changes Summary

**Before (with parsing logic in models.py):**
```python
class AgileTask(Task):
    sprint: str | None = None
    estimate: timedelta | None = None  # Required manual parsing
```

**After (with custom types):**
```python
from taskdantic import Task, TWDuration

class AgileTask(Task):
    sprint: str | None = None
    estimate: TWDuration | None = None  # Automatic parsing!
```

### Custom Types

- **TWDatetime**: Parses/serializes Taskwarrior timestamps (`YYYYMMDDTHHmmssZ`)
- **TWDuration**: Parses/serializes ISO 8601 durations (`PT#H#M#S`)
- **UUIDList**: Parses/serializes comma-separated UUID strings

### Usage Example

```python
from taskdantic import Task, TWDatetime, TWDuration, UUIDList

class AgileTask(Task):
    sprint: str | None = None
    points: int = 0
    estimate: TWDuration | None = None
    reviewed: TWDatetime | None = None
    blocked_by: UUIDList | None = None

# Automatic parsing
task = AgileTask(
    description="Feature",
    estimate="PT6H",                    # → timedelta(hours=6)
    reviewed="20240120T100000Z",        # → datetime(...)
    blocked_by="uuid1,uuid2"            # → [UUID(...), UUID(...)]
)

# Automatic serialization
exported = task.export_dict()
# {
#   "estimate": "PT6H",
#   "reviewed": "20240120T100000Z",
#   "blocked_by": "uuid1,uuid2"
# }
```

### Testing

After integration, run:
```bash
pytest tests/test_uda_inheritance.py -v
pytest tests/test_uda_integration.py -v
```

All tests should pass.

### Benefits

1. **User simplicity**: Just change type hints
2. **Full Pydantic validation**: Works with all Pydantic features
3. **Type safety**: IDE autocomplete and type checking
4. **Automatic format handling**: No manual parsing needed
5. **Standard Python types**: TWDatetime/TWDuration/UUIDList are subclasses of datetime/timedelta/list
