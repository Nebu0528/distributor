#!/usr/bin/env python3
"""
Stress Test: Compute-intensive benchmark with scaling curve.

Runs a heavy (but safe) workload and tests with 1, 2, 4, 6, and 8 workers
to show how speedup scales with worker count.

Workload: N-body gravity simulation (pure Python)
Each task simulates 500 particles for 100 timesteps — CPU-intensive
floating point math with no I/O or external dependencies.

Usage:
    python3 stress_test.py
"""

import time
import subprocess
import sys
import os

import logging
logging.disable(logging.CRITICAL)

from distributed_compute import Coordinator, Worker

# ── Config ───────────────────────────────────────────────────────────────────
NUM_TASKS = 48
COORDINATOR_PORT = 5580


# ── Workload: N-body gravity simulation ──────────────────────────────────────
def nbody_task(task_index):
    """Simulate N-body gravitational interaction. Pure CPU math."""
    import math
    import random

    num_particles = 500
    timesteps = 100
    dt = 0.01
    softening = 0.01

    rng = random.Random(task_index * 7919)

    # Initialize random positions and velocities
    px = [rng.uniform(-10, 10) for _ in range(num_particles)]
    py = [rng.uniform(-10, 10) for _ in range(num_particles)]
    pz = [rng.uniform(-10, 10) for _ in range(num_particles)]
    vx = [rng.uniform(-1, 1) for _ in range(num_particles)]
    vy = [rng.uniform(-1, 1) for _ in range(num_particles)]
    vz = [rng.uniform(-1, 1) for _ in range(num_particles)]
    mass = [rng.uniform(0.5, 2.0) for _ in range(num_particles)]

    total_energy = 0.0

    for step in range(timesteps):
        # Compute forces (O(n^2) pairwise gravity)
        ax = [0.0] * num_particles
        ay = [0.0] * num_particles
        az = [0.0] * num_particles

        for i in range(num_particles):
            for j in range(i + 1, num_particles):
                dx = px[j] - px[i]
                dy = py[j] - py[i]
                dz = pz[j] - pz[i]
                dist_sq = dx * dx + dy * dy + dz * dz + softening
                inv_dist = 1.0 / math.sqrt(dist_sq)
                inv_dist3 = inv_dist * inv_dist * inv_dist
                f = mass[j] * inv_dist3
                ax[i] += f * dx
                ay[i] += f * dy
                az[i] += f * dz
                f = mass[i] * inv_dist3
                ax[j] -= f * dx
                ay[j] -= f * dy
                az[j] -= f * dz

        # Update velocities and positions
        for i in range(num_particles):
            vx[i] += ax[i] * dt
            vy[i] += ay[i] * dt
            vz[i] += az[i] * dt
            px[i] += vx[i] * dt
            py[i] += vy[i] * dt
            pz[i] += vz[i] * dt

    # Compute final kinetic energy
    for i in range(num_particles):
        total_energy += 0.5 * mass[i] * (vx[i]**2 + vy[i]**2 + vz[i]**2)

    return {"task": task_index, "energy": round(total_energy, 4), "particles": num_particles, "steps": timesteps}


# ── Runner ───────────────────────────────────────────────────────────────────

def run_sequential():
    """Single-threaded baseline."""
    print(f"  Sequential ({NUM_TASKS} tasks)...", end="", flush=True)
    start = time.time()
    for i in range(NUM_TASKS):
        nbody_task(i)
    elapsed = time.time() - start
    print(f" {elapsed:.1f}s")
    return elapsed


def run_with_workers(num_workers, port):
    """Distributed with N worker processes."""
    coordinator = Coordinator(port=port, verbose=False)
    coordinator.start_server()

    procs = []
    for i in range(num_workers):
        p = subprocess.Popen(
            [sys.executable, "-c",
             f"import logging; logging.disable(logging.CRITICAL); "
             f"from distributed_compute import Worker; "
             f"w = Worker(coordinator_host='localhost', coordinator_port={port}, "
             f"max_concurrent_tasks=2, name='w-{i+1}'); w.start(block=True)"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        procs.append(p)

    # Wait for workers
    deadline = time.time() + 15
    while time.time() < deadline:
        if coordinator.get_stats()["workers"] >= num_workers:
            break
        time.sleep(0.3)

    n = coordinator.get_stats()["workers"]
    print(f"  {n} workers...", end="", flush=True)

    start = time.time()
    coordinator.map(nbody_task, list(range(NUM_TASKS)), timeout=600)
    elapsed = time.time() - start
    print(f" {elapsed:.1f}s")

    for p in procs:
        p.terminate()
    for p in procs:
        p.wait()
    coordinator.stop_server()
    time.sleep(0.5)

    return elapsed


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cpu_count = os.cpu_count() or 1

    print("\n" + "=" * 60)
    print("  STRESS TEST: N-Body Gravity Simulation")
    print("=" * 60)
    print(f"  CPU cores: {cpu_count}")
    print(f"  Tasks: {NUM_TASKS}  |  500 particles × 100 timesteps each")
    print(f"  Workload: O(n²) pairwise gravity — pure floating point\n")

    # Baseline
    baseline = run_sequential()

    # Scaling curve
    worker_counts = [1, 2, 4, 6, 8]
    results = []

    for n in worker_counts:
        port = COORDINATOR_PORT + n
        elapsed = run_with_workers(n, port)
        speedup = baseline / elapsed if elapsed > 0 else 0
        efficiency = (speedup / n) * 100
        results.append((n, elapsed, speedup, efficiency))

    # Summary
    print(f"\n{'='*60}")
    print(f"  SCALING RESULTS")
    print(f"{'='*60}")
    print(f"  {'Workers':>8} {'Time':>8} {'Speedup':>8} {'Efficiency':>11}")
    print(f"  {'─'*8} {'─'*8} {'─'*8} {'─'*11}")
    print(f"  {'1 (seq)':>8} {baseline:>7.1f}s {'1.00x':>8} {'100.0%':>11}")
    for n, elapsed, speedup, efficiency in results:
        print(f"  {n:>8} {elapsed:>7.1f}s {speedup:>7.2f}x {efficiency:>10.1f}%")
    print(f"{'='*60}\n")
