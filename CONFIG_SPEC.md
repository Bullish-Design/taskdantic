# CONFIG_SPEC.md

# Taskdantic Configuration Specification

## Overview

Taskdantic uses YAML as the primary configuration format, which is then converted to Taskwarrior's native `.taskrc` format. This approach provides a more structured, readable, and maintainable configuration experience.

## Architecture

```
taskdantic.yaml  →  TaskConfig  →  .taskrc
    (source)       (Python model)   (Taskwarrior format)
```

### Workflow

1. **Create** `taskdantic.yaml` with desired configuration
2. **Load** via `TaskConfig.from_yaml("taskdantic.yaml")`
3. **Write** to `.taskrc` via `config.write_taskrc("~/.taskrc")`
4. **Use** with TaskWarrior via `TaskWarrior(config_filename="~/.taskrc")`

## YAML Configuration Format

### Basic Structure

```yaml
# Data storage
data:
  location: ~/.task

# General settings
confirmation: false
verbose: true
hooks: false
context: null

# Nested configuration
json:
  array: true
  depends:
    array: false

# Color scheme
color:
  active: rgb555 on rgb410
  due: rgb550

# Reports
report:
  next:
    columns: id,description,priority
    filter: status:pending
    labels: ID,Description,Priority

# User-Defined Attributes
udas:
  estimate:
    type: numeric
    label: Estimate (hours)
  complexity:
    type: string
    label: Complexity
    values:
      - low
      - medium
      - high
```

### Conversion to .taskrc

The YAML structure is flattened to dot-notation key=value pairs:

```yaml
data:
  location: ~/.task
confirmation: false
```

Becomes:

```
data.location=~/.task
confirmation=off
```

## Configuration Sections

### 1. Data Location

```yaml
data:
  location: ~/.task  # Path to task database
```

**Conversion:** `data.location=~/.task`

### 2. General Settings

```yaml
confirmation: false  # Disable confirmation prompts
verbose: true        # Enable verbose output
hooks: false         # Disable hooks
context: null        # No default context
```

**Boolean Conversion:**
- `true` → `on`
- `false` → `off`
- `null` → empty value (`key=`)

### 3. JSON Configuration

```yaml
json:
  array: true        # Export tasks as JSON array
  depends:
    array: false     # Dependencies not as array
```

**Conversion:**
```
json.array=on
json.depends.array=off
```

### 4. Color Configuration

```yaml
color:
  active: rgb555 on rgb410
  completed: green
  due: bold red
  overdue: bold red on rgb500
  scheduled: white on rgb013
```

**Conversion:** Direct string mapping to `color.*` keys

### 5. Report Configuration

```yaml
report:
  next:
    columns: id,start.age,entry.age,depends,priority,project,tags,due,description
    labels: ID,Active,Age,Deps,P,Project,Tag,Due,Description
    filter: status:pending -WAITING
    sort: urgency-
  list:
    columns: id,description
    labels: ID,Description
    filter: status:pending
```

**Conversion:** Nested keys flatten to `report.next.columns`, etc.

### 6. User-Defined Attributes (UDAs)

UDAs require special handling and are defined under the `udas` key:

```yaml
udas:
  # Numeric UDA
  estimate:
    type: numeric
    label: Estimate (hours)
  
  # String UDA with values
  complexity:
    type: string
    label: Complexity
    values:
      - low
      - medium
      - high
  
  # Date UDA
  reviewed:
    type: date
    label: Last Reviewed
  
  # Duration UDA
  timespent:
    type: duration
    label: Time Spent
```

**Conversion:**
```
uda.estimate.type=numeric
uda.estimate.label=Estimate (hours)
uda.complexity.type=string
uda.complexity.label=Complexity
uda.complexity.values=low,medium,high
uda.reviewed.type=date
uda.reviewed.label=Last Reviewed
```

#### UDA Types

- **numeric**: Integer or decimal values
- **string**: Text values (optionally with predefined values list)
- **date**: Date values
- **duration**: Time duration values

#### Required vs Optional UDA Fields

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | UDA data type |
| `label` | No | Human-readable label |
| `values` | No | Predefined values (string type only) |

## API Reference

### TaskConfig Class

#### Loading from YAML

```python
from taskdantic import TaskConfig

# Load from YAML file
config = TaskConfig.from_yaml("taskdantic.yaml")

# Load from non-existent file (returns empty config)
config = TaskConfig.from_yaml("missing.yaml")
```

#### Writing to .taskrc

```python
# Write to .taskrc format
config.write_taskrc("~/.taskrc")
config.write_taskrc("/path/to/custom/.taskrc")
```

#### Accessing Configuration

```python
# Get nested values with dot notation
data_location = config.get("data.location")
report_filter = config.get("report.next.filter")

# Get with default value
timeout = config.get("limits.timeout", 30)

# Access data_location directly
location = config.data_location

# Get all UDAs
udas = config.get_udas()
# Returns: {"estimate": {"type": "numeric", "label": "Estimate"}, ...}

# Access specific UDA
estimate_uda = config.udas["estimate"]
print(estimate_uda.type)   # "numeric"
print(estimate_uda.label)  # "Estimate"
```

### TaskRcWriter Class

Low-level writer for YAML → .taskrc conversion:

```python
from taskdantic.config_writer import TaskRcWriter

writer = TaskRcWriter("taskdantic.yaml")
writer.write_taskrc("~/.taskrc")
```

### Helper Functions

```python
from taskdantic import create_default_yaml

# Create default YAML configuration file
create_default_yaml("taskdantic.yaml")
```

## Usage Examples

### Basic Setup

```python
from taskdantic import TaskConfig, TaskWarrior, create_default_yaml

# Create default configuration
create_default_yaml("taskdantic.yaml")

# Edit taskdantic.yaml as needed, then:

# Load config
config = TaskConfig.from_yaml("taskdantic.yaml")

# Write to .taskrc
config.write_taskrc("~/.taskrc")

# Use with TaskWarrior
tw = TaskWarrior(config_filename="~/.taskrc")
```

### Custom Configuration

```python
import yaml
from taskdantic import TaskConfig

# Create custom config
custom_config = {
    "data": {"location": "/custom/path/.task"},
    "confirmation": False,
    "udas": {
        "estimate": {"type": "numeric", "label": "Hours"},
        "priority_score": {"type": "numeric", "label": "Priority Score"},
    },
    "report": {
        "work": {
            "filter": "project:work status:pending",
            "columns": "id,description,estimate",
            "labels": "ID,Task,Hours",
        }
    },
}

# Write to YAML
with open("custom.yaml", "w") as f:
    yaml.safe_dump(custom_config, f)

# Load and use
config = TaskConfig.from_yaml("custom.yaml")
config.write_taskrc("~/.taskrc")
```

### Testing Configuration

```python
from pathlib import Path
from taskdantic import TaskConfig

# Use isolated config for testing
test_config = {
    "data": {"location": "/tmp/test-tasks"},
    "confirmation": False,
    "hooks": False,
}

# Write test YAML
test_yaml = Path("/tmp/test-config.yaml")
import yaml
with open(test_yaml, "w") as f:
    yaml.safe_dump(test_config, f)

# Load and convert
config = TaskConfig.from_yaml(test_yaml)
config.write_taskrc("/tmp/.taskrc")
```

## Type Conversions

### Python → YAML → .taskrc

| Python Type | YAML Representation | .taskrc Format |
|------------|---------------------|----------------|
| `bool` | `true`/`false` | `on`/`off` |
| `None` | `null` | `` (empty) |
| `str` | `"string"` | `string` |
| `int` | `123` | `123` |
| `float` | `1.5` | `1.5` |
| `list` | `[a, b, c]` | `a,b,c` |
| `dict` | Nested structure | Dot notation |

### Examples

```yaml
# YAML
confirmation: false
timeout: 30
description: "Test project"
tags: [work, urgent]
data:
  location: ~/.task
```

```
# .taskrc
confirmation=off
timeout=30
description=Test project
tags=work,urgent
data.location=~/.task
```

## Migration from .taskrc

To migrate existing `.taskrc` to YAML format:

1. **Manual conversion**: Review your `.taskrc` and convert to YAML structure
2. **Group related settings**: Organize into nested YAML structure
3. **Extract UDAs**: Move UDA definitions to `udas` section
4. **Test**: Load YAML, write to temporary .taskrc, verify with `task show`

### Example Migration

**Original .taskrc:**
```
data.location=/home/user/.task
confirmation=off
uda.estimate.type=numeric
uda.estimate.label=Estimate
color.active=rgb555
```

**New taskdantic.yaml:**
```yaml
data:
  location: /home/user/.task
confirmation: false
color:
  active: rgb555
udas:
  estimate:
    type: numeric
    label: Estimate
```

## Best Practices

1. **Version Control**: Keep `taskdantic.yaml` in version control
2. **Comments**: Use YAML comments to document custom settings
3. **Validation**: Load and write to test .taskrc before deploying
4. **Backup**: Keep backup of working `.taskrc` before switching
5. **UDA Organization**: Group related UDAs together
6. **Naming**: Use descriptive UDA names and labels

## Limitations

1. **Include Directives**: YAML doesn't support `.taskrc` `include` directives (use YAML anchors/aliases instead)
2. **One-Way Conversion**: Library converts YAML → .taskrc only, not .taskrc → YAML
3. **Config Overrides**: Use `TaskWarrior(config_overrides={})` for runtime overrides instead of modifying YAML

## Troubleshooting

### YAML Won't Load

```python
import yaml

# Validate YAML syntax
with open("taskdantic.yaml") as f:
    try:
        config = yaml.safe_load(f)
        print("Valid YAML")
    except yaml.YAMLError as e:
        print(f"YAML Error: {e}")
```

### .taskrc Not Generated Correctly

```python
config = TaskConfig.from_yaml("taskdantic.yaml")

# Check loaded config
print(config.config)
print(config.udas)
print(config.data_location)

# Generate and inspect
config.write_taskrc("/tmp/.taskrc")
with open("/tmp/.taskrc") as f:
    print(f.read())
```

### UDAs Not Working

Verify UDA structure in YAML:
```yaml
udas:
  myuda:
    type: string  # Must have type
    label: My UDA  # Optional but recommended
```

Check generated .taskrc contains:
```
uda.myuda.type=string
uda.myuda.label=My UDA
```

## Complete Example

```yaml
# taskdantic.yaml - Complete configuration example

# Core settings
data:
  location: ~/.task

confirmation: false
verbose: false
hooks: true
context: work

# JSON export settings
json:
  array: true
  depends:
    array: false

# Color scheme
color:
  active: rgb555 on rgb410
  completed: green
  deleted: red
  due: rgb550
  due.today: bold red
  overdue: bold red on rgb500
  scheduled: white on rgb013
  recurring: magenta
  tagged: cyan
  uda.priority.H: bold red
  uda.priority.M: yellow
  uda.priority.L: blue

# Reports
report:
  next:
    columns: id,start.age,entry.age,depends,priority,project,tags,recur,scheduled.countdown,due.relative,until.remaining,description,urgency
    labels: ID,Active,Age,Deps,P,Project,Tag,Recur,S,Due,Until,Description,Urg
    filter: status:pending limit:page
    sort: urgency-

  work:
    columns: id,description,priority,estimate,project,tags
    labels: ID,Task,P,Est,Project,Tags
    filter: project:work status:pending
    sort: priority-,due+

# User-Defined Attributes
udas:
  estimate:
    type: numeric
    label: Estimate (hours)
  
  complexity:
    type: string
    label: Complexity
    values:
      - low
      - medium
      - high
  
  reviewed:
    type: date
    label: Last Reviewed
  
  billable:
    type: string
    label: Billable
    values:
      - yes
      - no

# Search settings
search:
  case:
    sensitive: false

# Urgency coefficients
urgency:
  active:
    coefficient: 4.0
  blocked:
    coefficient: -5.0
  tags:
    coefficient: 1.0
  project:
    coefficient: 1.0
  due:
    coefficient: 12.0
```

## See Also

- [Taskwarrior Documentation](https://taskwarrior.org/docs/)
- [YAML Specification](https://yaml.org/spec/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
