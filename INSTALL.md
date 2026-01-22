# Installation Guide

## Install from Source

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/distributed-compute-locally.git
cd distributed-compute-locally
```

### 2. Install in Development Mode
```bash
pip install -e .
```

This installs the package in "editable" mode, allowing you to make changes to the code.

### 3. Install with Development Tools
```bash
pip install -e ".[dev]"
```

This includes pytest, black, flake8, etc.

## Install from PyPI (Future)

Once published to PyPI, you can install with:
```bash
pip install distributed-compute-locally
```

## Usage After Installation

After installation, you can use the `distcompute` command from anywhere:

### Start Coordinator
```bash
distcompute coordinator
```

### Start Worker
```bash
distcompute worker <coordinator-ip>
```

### Run Demo
```bash
distcompute demo
```

## Using as a Library

```python
from distributed_compute import Coordinator, Worker

# Start coordinator
coordinator = Coordinator(port=5555)
coordinator.start()

# Define your function
def compute_task(x):
    return x ** 2

# Distribute work
results = coordinator.map(compute_task, range(100))
print(results)
```

## Build Distribution Package

To build a distribution package for PyPI:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# This creates:
# - dist/distributed_compute_locally-0.1.0.tar.gz (source)
# - dist/distributed_compute_locally-0.1.0-py3-none-any.whl (wheel)
```

## Upload to PyPI (Maintainers Only)

```bash
# Test PyPI (for testing)
twine upload --repository testpypi dist/*

# Production PyPI
twine upload dist/*
```

## Verify Installation

```bash
# Check if installed
pip show distributed-compute-locally

# Test the CLI
distcompute --help

# Run demo
distcompute demo
```

## Uninstall

```bash
pip uninstall distributed-compute-locally
```

## Development Setup

```bash
# Clone and install in dev mode
git clone https://github.com/yourusername/distributed-compute-locally.git
cd distributed-compute-locally
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Lint code
flake8 distributed_compute/
```
