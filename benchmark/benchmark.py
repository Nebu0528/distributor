#!/usr/bin/env python3
"""
Benchmark Suite for distributed-compute-locally

Three standard benchmarks, each run single-threaded then distributed:
  1. NAS EP  — NASA Embarrassingly Parallel (Gaussian pair computation)
  2. Mandelbrot — Classic fractal pixel computation
  3. SHA-256 Search — Brute-force hash prefix search

Tuned for M2 MacBook (8 cores). Each task takes ~1s so total baseline ~30s per benchmark.

Usage:
    python3 benchmark.py [num_workers]    # default: 4 workers
"""

import time
import threading
import subprocess
import signal
import sys
import os

import logging
logging.disable(logging.CRITICAL)  # Suppress coordinator/worker log noise

from distributed_compute import Coordinator, Worker

# ── Config ───────────────────────────────────────────────────────────────────
NUM_TASKS = 24
NUM_WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 4
COORDINATOR_PORT = 5570


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK 1: NAS EP (Embarrassingly Parallel)
# Based on the NASA NAS Parallel Benchmark EP kernel.
# Generates random (X, Y) Gaussian pairs using the Marsaglia polar method
# and counts how many fall into successive annular regions around the origin.
# Reference: https://www.nas.nasa.gov/software/npb.html
# ═══════════════════════════════════════════════════════════════════════════════

def nas_ep_task(task_index):
    """NAS EP kernel: generate Gaussian pairs, classify into annular regions."""
    import random
    num_pairs = 500_000
    # 10 annular regions: 0 <= r^2 < 1, 1 <= r^2 < 2, ..., 9 <= r^2 < 10
    counts = [0] * 10
    sx = 0.0
    sy = 0.0

    rng = random.Random(task_index * 31337)

    pairs_generated = 0
    while pairs_generated < num_pairs:
        # Marsaglia polar method for generating Gaussian pairs
        x1 = 2.0 * rng.random() - 1.0
        x2 = 2.0 * rng.random() - 1.0
        s = x1 * x1 + x2 * x2
        if s >= 1.0 or s == 0.0:
            continue
        import math
        t = math.sqrt(-2.0 * math.log(s) / s)
        gx = x1 * t
        gy = x2 * t
        sx += gx
        sy += gy
        r2 = gx * gx + gy * gy
        idx = int(r2)
        if 0 <= idx < 10:
            counts[idx] += 1
        pairs_generated += 1

    return {"task": task_index, "pairs": num_pairs, "sx": round(sx, 4), "sy": round(sy, 4), "counts": counts}


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK 2: Mandelbrot Set
# Classic embarrassingly parallel benchmark. Each task computes a horizontal
# strip of the Mandelbrot set at 2048x2048 resolution, 256 max iterations.
# Commonly used in Dask/Ray/Spark comparisons.
# ═══════════════════════════════════════════════════════════════════════════════

def mandelbrot_task(strip_index):
    """Compute a horizontal strip of the Mandelbrot set."""
    width = 2048
    height = 2048
    max_iter = 256
    strips = 24  # must match NUM_TASKS
    rows_per_strip = height // strips
    y_start = strip_index * rows_per_strip
    y_end = y_start + rows_per_strip

    total_iters = 0
    pixels_inside = 0

    for py in range(y_start, y_end):
        y0 = (py / height) * 3.0 - 1.5
        for px in range(width):
            x0 = (px / width) * 3.5 - 2.5
            x = 0.0
            y = 0.0
            iteration = 0
            while x * x + y * y <= 4.0 and iteration < max_iter:
                xtemp = x * x - y * y + x0
                y = 2.0 * x * y + y0
                x = xtemp
                iteration += 1
            total_iters += iteration
            if iteration == max_iter:
                pixels_inside += 1

    return {"strip": strip_index, "total_iters": total_iters, "pixels_inside": pixels_inside}


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK 3: SHA-256 Brute-Force Search
# Each task tries N candidates looking for the hash with the most leading zeros.
# Practical workload similar to proof-of-work / password cracking.
# ═══════════════════════════════════════════════════════════════════════════════

def sha256_task(task_index):
    """Brute-force SHA-256: find the candidate with the lowest hash value."""
    import hashlib
    candidates = 500_000
    best_hash = "f" * 64
    best_input = ""
    prefix = f"block{task_index}_nonce"

    for i in range(candidates):
        candidate = f"{prefix}{i}"
        h = hashlib.sha256(candidate.encode()).hexdigest()
        if h < best_hash:
            best_hash = h
            best_input = candidate

    leading_zeros = len(best_hash) - len(best_hash.lstrip("0"))
    return {"task": task_index, "best_hash": best_hash[:16], "leading_zeros": leading_zeros}


# ═══════════════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════════════

def run_sequential(name, func, tasks):
    """Run tasks sequentially (single-threaded baseline)."""
    print(f"  Sequential ({NUM_TASKS} tasks)...", end="", flush=True)
    start = time.time()
    results = []
    for i, t in enumerate(tasks):
        results.append(func(t))
    elapsed = time.time() - start
    print(f" {elapsed:.2f}s")
    return elapsed


def run_distributed(name, func, tasks, port):
    """Run tasks distributed across local workers (separate processes to bypass GIL)."""
    coordinator = Coordinator(port=port, verbose=False)
    coordinator.start_server()

    # Spawn workers as separate OS processes so each gets its own GIL
    worker_procs = []
    for i in range(NUM_WORKERS):
        p = subprocess.Popen(
            [sys.executable, "-c",
             f"from distributed_compute import Worker; "
             f"w = Worker(coordinator_host='localhost', coordinator_port={port}, "
             f"max_concurrent_tasks=2, name='worker-{i+1}'); w.start(block=True)"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        worker_procs.append(p)

    # Wait for workers to register
    deadline = time.time() + 15
    while time.time() < deadline:
        stats = coordinator.get_stats()
        if stats["workers"] >= NUM_WORKERS:
            break
        time.sleep(0.3)

    n_workers = coordinator.get_stats()["workers"]
    print(f"  Distributed ({n_workers} workers, {NUM_TASKS} tasks)...", end="", flush=True)

    start = time.time()
    results = coordinator.map(func, tasks, timeout=300)
    elapsed = time.time() - start
    print(f" {elapsed:.2f}s")

    # Worker breakdown
    stats = coordinator.get_stats()
    if stats.get("worker_details"):
        for w in stats["worker_details"]:
            print(f"    {w['name']:<12} {w['tasks_completed']:>2} tasks")

    # Kill worker processes
    for p in worker_procs:
        p.terminate()
    for p in worker_procs:
        p.wait()
    coordinator.stop_server()
    time.sleep(0.5)

    return elapsed


def run_benchmark(name, func, tasks, port):
    """Run one benchmark: sequential then distributed."""
    print(f"\n{'─'*60}")
    print(f"  {name}")
    print(f"{'─'*60}")

    seq_time = run_sequential(name, func, tasks)
    dist_time = run_distributed(name, func, tasks, port)
    speedup = seq_time / dist_time if dist_time > 0 else 0

    print(f"  Speedup: {speedup:.2f}x")
    return seq_time, dist_time, speedup


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    cpu_count = os.cpu_count() or 1

    print("\n" + "=" * 60)
    print("  DISTRIBUTED COMPUTE LOCALLY — BENCHMARK SUITE")
    print("=" * 60)
    print(f"  CPU cores: {cpu_count}  |  Workers: {NUM_WORKERS}  |  Tasks per benchmark: {NUM_TASKS}")

    task_list = list(range(NUM_TASKS))

    benchmarks = [
        ("NAS EP — Gaussian Pair Generation (NASA)", nas_ep_task, task_list, COORDINATOR_PORT),
        ("Mandelbrot Set — 2048x2048, 256 iters", mandelbrot_task, task_list, COORDINATOR_PORT + 1),
        ("SHA-256 Search — Brute-Force Hash", sha256_task, task_list, COORDINATOR_PORT + 2),
    ]

    results = []
    for name, func, tasks, port in benchmarks:
        seq, dist, speedup = run_benchmark(name, func, tasks, port)
        results.append((name, seq, dist, speedup))

    # Summary
    print(f"\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Benchmark':<42} {'Seq':>6} {'Dist':>6} {'Speedup':>8}")
    print(f"  {'─'*42} {'─'*6} {'─'*6} {'─'*8}")
    for name, seq, dist, speedup in results:
        short = name.split("—")[0].strip()
        print(f"  {short:<42} {seq:>5.1f}s {dist:>5.1f}s {speedup:>6.2f}x")
    print(f"  {'─'*42} {'─'*6} {'─'*6} {'─'*8}")
    avg_speedup = sum(r[3] for r in results) / len(results)
    print(f"  {'Average':<42} {'':>6} {'':>6} {avg_speedup:>6.2f}x")
    print(f"\n  Machine: Apple M2, {cpu_count} cores")
    print(f"  Workers: {NUM_WORKERS}")
    print(f"{'='*60}\n")
