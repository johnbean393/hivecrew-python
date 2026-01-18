# Hivecrew Python SDK

A Python client library for the [Hivecrew](https://hivecrew.app) REST API, enabling programmatic control of computer-use agent tasks.

## Installation

```bash
pip install hivecrew
```

For development:

```bash
git clone https://github.com/hivecrew/hivecrew-python.git
cd hivecrew-python
pip install -e ".[dev]"
```

## Quick Start

### Setup

1. Enable the API server in Hivecrew → Settings → API
2. Generate an API key and set it as an environment variable:

```bash
export HIVECREW_API_KEY="hc_your_api_key_here"
```

### Basic Usage

```python
from hivecrew import HivecrewClient

# Initialize the client
client = HivecrewClient()  # Uses HIVECREW_API_KEY env var

# Or provide the API key directly
client = HivecrewClient(api_key="hc_xxx")
```

### Running a Task (Blocking)

The `run()` method creates a task and waits for it to complete:

```python
task = client.tasks.run(
    description="Open Safari and search for Python tutorials",
    provider_name="OpenRouter",
    model_id="anthropic/claude-sonnet-4.5",
    poll_interval=5.0,   # Check status every 5 seconds
    timeout=1200.0       # Fail after 20 minutes
)

print(f"Task {task.status}: {task.result_summary}")
print(f"Success: {task.was_successful}")
print(f"Steps: {task.step_count}, Duration: {task.duration}s")
```

### Creating a Task (Non-Blocking)

The `create()` method returns immediately:

```python
task = client.tasks.create(
    description="Download quarterly reports from the finance portal",
    provider_name="OpenRouter",
    model_id="anthropic/claude-sonnet-4.5"
)

print(f"Task created: {task.id}")
print(f"Status: {task.status}")  # "queued"
```

### Uploading Files with a Task

```python
task = client.tasks.create(
    description="Analyze this spreadsheet and create a summary",
    provider_name="OpenRouter",
    model_id="anthropic/claude-sonnet-4.5",
    files=["./data/report.xlsx", "./data/notes.pdf"]
)
```

### Listing and Filtering Tasks

```python
# List recent tasks
result = client.tasks.list(limit=10)
for task in result.tasks:
    print(f"{task.id}: {task.status} - {task.title}")

# Filter by status
running = client.tasks.list(status=["running", "queued"])
completed = client.tasks.list(status=["completed"], order="desc")
```

### Task Actions

```python
# Cancel a task
client.tasks.cancel(task_id)

# Pause a running task
client.tasks.pause(task_id)

# Resume with optional new instructions
client.tasks.resume(task_id, instructions="Also take a screenshot when done")
```

### Working with Task Files

```python
# List files associated with a task
files = client.tasks.list_files(task_id)

for f in files.input_files:
    print(f"Input: {f.name} ({f.size} bytes)")

for f in files.output_files:
    print(f"Output: {f.name} ({f.size} bytes)")

# Download an output file
path = client.tasks.download_file(
    task_id,
    "screenshot.png",
    "./downloads/"
)
print(f"Downloaded to {path}")
```

### Providers and Models

```python
# List available providers
providers = client.providers.list()
for p in providers.providers:
    print(f"{p.display_name} (default: {p.is_default})")

# List models for a provider
models = client.providers.list_models(provider_id)
for m in models.models:
    print(f"{m.id}: {m.context_length} tokens")
```

### VM Templates

```python
templates = client.templates.list()
print(f"Default template: {templates.default_template_id}")

for t in templates.templates:
    print(f"{t.name}: {t.description}")
```

### System Status

```python
status = client.system.status()
print(f"Server: {status.status} (v{status.version})")
print(f"Agents: {status.agents.running}/{status.agents.max_concurrent} running")
print(f"VMs: {status.vms.active} active, {status.vms.available} available")

config = client.system.config()
print(f"Max concurrent VMs: {config.max_concurrent_vms}")
print(f"Default timeout: {config.default_timeout_minutes} minutes")
```

### Health Check

```python
if client.health_check():
    print("Hivecrew server is running")
else:
    print("Server is not responding")
```

## Configuration

### Client Options

```python
client = HivecrewClient(
    api_key="hc_xxx",                           # API key (or use env var)
    base_url="http://192.168.1.100:5482/api/v1", # Custom server URL
    timeout=60.0                                 # Request timeout in seconds
)
```

### Context Manager

```python
with HivecrewClient() as client:
    task = client.tasks.run(
        description="Take a screenshot",
        provider_name="OpenRouter",
        model_id="anthropic/claude-sonnet-4.5"
    )
# Session is automatically closed
```

## Error Handling

```python
from hivecrew import (
    HivecrewError,
    AuthenticationError,
    NotFoundError,
    BadRequestError,
    ConflictError,
    TaskTimeoutError,
)

try:
    task = client.tasks.run(
        description="Do something",
        provider_name="OpenRouter",
        model_id="anthropic/claude-sonnet-4.5",
        timeout=60.0
    )
except AuthenticationError:
    print("Invalid API key")
except NotFoundError:
    print("Resource not found")
except ConflictError as e:
    print(f"Action not allowed: {e.message}")
except TaskTimeoutError as e:
    print(f"Task {e.task_id} didn't complete in {e.timeout}s")
except HivecrewError as e:
    print(f"API error: {e.message}")
```

## Task Status Values

| Status | Description |
|--------|-------------|
| `queued` | Waiting to start |
| `waitingForVM` | Waiting for a VM to become available |
| `running` | Currently executing |
| `paused` | Paused, waiting for user action |
| `completed` | Finished successfully |
| `failed` | Failed with an error |
| `cancelled` | Cancelled by user |
| `timedOut` | Exceeded time limit |
| `maxIterations` | Exceeded iteration limit |

## Requirements

- Python 3.9+
- Hivecrew app with API server enabled

## License

MIT License - see [LICENSE](LICENSE) for details.
