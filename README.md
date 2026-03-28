[![PyPI](https://img.shields.io/pypi/v/distributed-compute-locally.svg)](https://pypi.org/project/distributed-compute-locally/) [![Downloads](https://static.pepy.tech/badge/distributed-compute-locally)](https://pepy.tech/project/distributed-compute-locally) [![Downloads](https://static.pepy.tech/badge/distributed-compute-locally/month)](https://pepy.tech/project/distributed-compute-locally) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Distributed Compute

A Python library for distributing computational workloads across multiple devices on a local network. Allows you to utilize your spare computers
into a computing cluster to perform complex tasks that would require a lot of computing power and making it easy to connect devices locally.

## Features

- **Interactive CLI** - For monitoring worker health (CPU usage, task counts, active workers), and trigger Python script runs.
- **Load Balancing** - Tasks distributed to least-loaded workers
- **Fault Tolerance** - Automatic task redistribution on worker failure
- **Authentication** - Coordinator can now create a password that is required for the workers to connect to.
- **Task Retry** - Configurable automatic retries for failed tasks before giving up

## Installation

Install via pip (Python 3.7+):

```bash
pip install distributed-compute-locally
```

## Quick Start

### 1. Start the Coordinator

On your main machine:

```bash
distcompute coordinator
```

This starts an **interactive coordinator** with a beautiful CLI where you can run commands, check status, and execute tasks directly.

### 2. Connect Workers

On each worker machine (laptops, desktops, etc.):

```bash
distcompute worker <coordinator-ip>
```

Or on the same machine for local testing:
```bash
distcompute worker
# Defaults to localhost
```

Example with remote coordinator:
```bash
distcompute worker 192.168.1.100
```

### 3. Run Your Computation

```python
from distributed_compute import Coordinator

# Initialize coordinator
coordinator = Coordinator(port=5555)
coordinator.start()

# Define your compute function
def heavy_computation(x):
    return x ** 2

# Distribute work across all connected workers
results = coordinator.map(heavy_computation, range(1000))
print(results)  # [0, 1, 4, 9, 16, ...]
```

That's it! Your computation is now running across all connected machines.

## CLI Commands

The `distcompute` command provides several options:

```bash
# Start coordinator (with interactive mode)
distcompute coordinator [port]

# Connect worker (host defaults to localhost)
distcompute worker [host] [port] [name]

# Run demo
distcompute demo
```


When you start the coordinator, it now launches an **interactive terminal** with a beautiful CLI interface (powered by Rich and prompt_toolkit):

```bash
distcompute coordinator
```

You'll see a prompt where you can run commands:

```
distcompute> help

Available Commands:
  run <file.py>  - Execute a task file across workers
  status         - Show cluster status with worker stats
  help           - Show this help message
  exit           - Shutdown coordinator
```

**Example task file**:
```python
def monte_carlo_pi(num_samples):
    import random
    inside = 0
    for _ in range(num_samples):
        x, y = random.random(), random.random()
        if x*x + y*y <= 1.0:
            inside += 1
    return inside

TASK_FUNC = monte_carlo_pi
ITERABLE = [1_000_000 for _ in range(20)]  # 20 tasks, each with 1 million samples

```

**Running tasks interactively**:
```
distcompute> status
┌─────────────────────────────────────┐
│         Cluster Status              │
├────────────────┬────────────────────┤
│ Metric         │ Value              │
├────────────────┼────────────────────┤
│ Workers        │ 2                  │
│ Tasks Pending  │ 0                  │
│ Tasks Completed│ 20                 │
└────────────────┴────────────────────┘

┌────────────────────────────────────────────────────────┐
│              Worker Details                            │
├──────────────┬────────────┬─────────────┬──────────────┤
│ Worker       │ CPU %      │ Tasks Done  │ Active       │
├──────────────┼────────────┼─────────────┼──────────────┤
│ worker-1     │ 25.4%      │ 12          │ 0            │
│ worker-2     │ 18.7%      │ 8           │ 0            │
└──────────────┴────────────┴─────────────┴──────────────┘

distcompute> run my_task.py
Running my_task.py across 2 worker(s)...
✓ Results: [0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, ...]

distcompute> exit
Shutting down coordinator...
```


## Task Retry

Failed tasks can be automatically retried with the `max_retries` parameter:

```python
# Retry each failed task up to 3 times before giving up
results = coordinator.map(heavy_computation, range(1000), max_retries=3)
```

When a task fails:
- If `max_retries > 0` and retries remain, the task is re-queued and sent to an available worker
- If all retries are exhausted, the result for that task is `None`
- With the default `max_retries=0`, behavior is unchanged from previous versions

This is useful for transient failures (network hiccups, temporary resource exhaustion, etc.).

## Requirements

- Python 3.7 or higher
- Network connectivity between machines
- Same Python environment on all workers (recommended)
- `prompt_toolkit>=3.0.0` and `rich>=13.0.0` (auto-installed for interactive CLI)


## Troubleshooting

**Workers not connecting?**
- Ensure port 5555 (default) is open on the coordinator machine
- Check firewall settings
- Verify machines are on the same network
- Try specifying IP explicitly: `distcompute worker 192.168.1.100`

**Tasks failing?**
- Ensure all workers have required dependencies installed
- Check worker logs for error messages
- Verify functions are serializable (no lambdas with external state)

## Contributing

Contributions are welcome! This project aims to make distributed computing accessible to everyone.

## License

MIT License - see LICENSE file for details.

## Changelog

### v0.1.7
- **Task Retry** - Added `max_retries` parameter to `coordinator.map()` for automatic retry of failed tasks
- **Bug Fix** - Fixed version mismatch across `__init__.py`, `pyproject.toml`, and `setup.py`
- **Bug Fix** - Fixed default port inconsistency (now consistently `5555` everywhere)
- **Bug Fix** - Fixed `.gitignore` incorrectly excluding the `tests/` directory from git tracking

### v0.1.6
- Large payload handling with chunked transmission and zlib compression

### v0.1.5
- Password authentication for coordinator-worker connections

### v0.1.4
- Interactive CLI with Rich UI and worker statistics

### v0.1.2
- Progress callbacks (`on_progress`, `on_task_complete`)

## Acknowledgments

This project is heavily inspired by `Dask`, and powered by Python's `cloudpickle` for function serialization, `psutil` for resource monitoring, `Rich` and `prompt_toolkit` for providing a live cluster dashboard (CPU/Memory/Task stats).


