# Distributed Compute

A Python library for distributing computational workloads across multiple machines on a local network.

## Installation

```bash
pip install -e .
```

## Quick Start

### Starting the Coordinator

```bash
python cli.py coordinator
```

### Starting Workers

On each worker machine:

```bash
python start_worker.py <worker-name> <coordinator-ip>
```

Example:
```bash
python start_worker.py laptop-1 192.168.1.100
```

### Running Computations

```python
from distributed_compute import Coordinator

# Connect to coordinator
coordinator = Coordinator(port=5555, verbose=False)

# Define your task
def heavy_computation(x):
    return x ** 2

# Distribute work
results = coordinator.map(heavy_computation, range(100))
print(results)
```

Or use the provided script:
```bash
python run_computation.py
```

## Examples

See the `examples/` directory:
- `basic_usage.py` - Simple distributed computing
- `ml_inference.py` - ML model inference simulation
- `data_processing.py` - Data processing pipeline

## Features

- Load balancing across workers
- Automatic task redistribution on worker failure
- Real-time monitoring
- Simple API

## Requirements

- Python 3.7+
- Network connectivity between machines

## License

MIT
