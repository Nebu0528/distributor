[![PyPI](https://img.shields.io/pypi/v/distributed-compute-locally.svg)](https://pypi.org/project/distributed-compute-locally/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Distributed Compute Locally

The simplest way to distribute Python work across your local machines. No cluster config, no cloud, no complexity — just `pip install` and go.

Turn your spare laptops and desktops into a computing cluster over your local network. If you know `multiprocessing.Pool.map()`, you already know how to use this.

## When to Use This (and When Not To)

**Use this when:**
- You have idle machines on your network and want to put them to work
- You want distributed computing without learning Kubernetes, Spark, or cloud APIs
- You need something running in under 60 seconds, not 60 minutes of config

**Use Dask/Ray instead when:**
- You need advanced scheduling, task graphs, or GPU support
- You're running in production at scale
- You need a mature ecosystem with integrations

## Quick Start

**1. Install** (Python 3.7+):
```bash
pip install distributed-compute-locally
```

**2. Start a coordinator** on your main machine:
```bash
distcompute coordinator
```

**3. Connect workers** from other machines on the same network:
```bash
distcompute worker 192.168.1.100
```

**4. Distribute work:**
```python
from distributed_compute import Coordinator

coordinator = Coordinator()
coordinator.start_server()

def process(x):
    # your CPU-intensive work here
    return x ** 2

results = coordinator.map(process, range(1000))
# [0, 1, 4, 9, 16, ...] — computed across all connected machines
```

That's it. Three commands and you have a working cluster.

## Features

- **`coordinator.map(func, iterable)`** — same interface as `multiprocessing.Pool.map`, but across machines
- **Load balancing** — tasks routed to least-loaded workers automatically
- **Fault tolerance** — dead workers detected via heartbeat; their tasks get redistributed
- **Task retry** — failed tasks automatically retried up to `max_retries` times before giving up
- **Password auth** — optional `--password` flag to restrict who can join your cluster
- **Interactive CLI** — Rich-powered dashboard to monitor workers, view stats, and run tasks live
- **Large payload support** — chunked transmission with zlib compression for payloads over 512KB

## Task Retry

```python
# Retry each failed task up to 3 times before returning None
results = coordinator.map(func, data, max_retries=3)
```

Useful for transient failures — network hiccups, temporary resource exhaustion, flaky dependencies.

## CLI Usage

```bash
distcompute coordinator [port] [--password <pass>]   # start coordinator
distcompute worker [host] [port] [--password <pass>]  # connect a worker
distcompute demo                                       # run a self-contained demo
```

The coordinator launches an interactive prompt:

```
distcompute> status        # view cluster health + worker stats
distcompute> run task.py   # execute a task file across workers
distcompute> help          # list commands
distcompute> exit          # shutdown
```

**Task files** define `TASK_FUNC` and `ITERABLE`:
```python
import hashlib

def brute_force_hash(prefix):
    for i in range(1_000_000):
        candidate = f"{prefix}{i}"
        if hashlib.sha256(candidate.encode()).hexdigest()[:5] == "00000":
            return candidate
    return None

TASK_FUNC = brute_force_hash
ITERABLE = [f"block_{i}_" for i in range(100)]
```

## Requirements

- Python 3.7+
- Machines on the same network (or reachable via IP)
- Same Python environment on all workers (recommended)

## Troubleshooting

**Workers not connecting?**
- Ensure port 5555 (default) is open on the coordinator
- Check firewall settings
- Verify machines are on the same network
- Try specifying IP explicitly: `distcompute worker 192.168.1.100`

**Tasks failing?**
- Ensure all workers have required dependencies installed
- Check worker logs for error messages
- Functions must be serializable (no lambdas referencing external state)

## Contributing

Contributions welcome. Open an issue or submit a PR.

## License

MIT — see [LICENSE](LICENSE).

## Changelog

### v0.1.7
- **Task Retry** — `max_retries` parameter on `coordinator.map()` for automatic retry of failed tasks
- **Bug Fix** — Fixed version mismatch across package files
- **Bug Fix** — Default port now consistently `5555` everywhere
- **Bug Fix** — `.gitignore` no longer excludes test directory

### v0.1.6
- Large payload handling with chunked transmission and zlib compression

### v0.1.5
- Password authentication for coordinator-worker connections

### v0.1.4
- Interactive CLI with Rich UI and worker statistics

### v0.1.2
- Progress callbacks (`on_progress`, `on_task_complete`)


