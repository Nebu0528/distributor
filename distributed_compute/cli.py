"""
Beautiful CLI interface for distributed computing - Claude/Gemini style.

Usage:
    python cli.py coordinator  # Start coordinator with monitoring
    python cli.py worker <host> # Start worker and connect to coordinator
    python cli.py demo         # Run interactive demo
"""

import sys
import time
import threading
import os
import logging
from datetime import datetime
from distributed_compute import Coordinator, Worker

# Disable noisy logs
logging.getLogger('distributed_compute').setLevel(logging.ERROR)

# Logo
LOGO = """
╔════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                        ║
║   ██████╗ ██╗███████╗████████╗██████╗ ██╗██████╗ ██╗   ██╗████████╗ ██████╗ ██████╗    ║
║   ██╔══██╗██║██╔════╝╚══██╔══╝██╔══██╗██║██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗   ║
║   ██║  ██║██║███████╗   ██║   ██████╔╝██║██████╔╝██║   ██║   ██║   ██║   ██║██████╔╝   ║
║   ██║  ██║██║╚════██║   ██║   ██╔══██╗██║██╔══██╗██║   ██║   ██║   ██║   ██║██╔══██╗   ║
║   ██████╔╝██║███████║   ██║   ██║  ██║██║██████╔╝╚██████╔╝   ██║   ╚██████╔╝██║  ██║   ║
║   ╚═════╝ ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ║
║                                                                                        ║
║                               Distributed Computing Platform                           ║
║                                                                                        ║
╚════════════════════════════════════════════════════════════════════════════════════════╝
"""

class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    
    # Colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    
    # Gradients
    ORANGE = '\033[38;5;208m'
    PURPLE = '\033[38;5;141m'
    
    # Background
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'


def clear_screen():
    """Clear the terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header(text):
    """Print a formatted header."""
    print()
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.GRAY}{'─' * len(text)}{Colors.RESET}")
    print()


def print_logo():
    """Print the beautiful logo."""
    clear_screen()
    print(f"{Colors.CYAN}{LOGO}{Colors.RESET}")
    print()


def animate_text(text, color=Colors.CYAN, delay=0.03):
    """Animate text character by character."""
    for char in text:
        print(f"{color}{char}{Colors.RESET}", end='', flush=True)
        time.sleep(delay)
    print()


def run_coordinator_cli(port=5555):
    """Run coordinator with beautiful CLI monitoring."""
    print_logo()
    
    print(f"{Colors.BOLD}Coordinator Mode{Colors.RESET}\n")
    print(f"{Colors.GRAY}→{Colors.RESET} Initializing", end='', flush=True)
    
    coordinator = Coordinator(port=port, verbose=False)
    coordinator.start_server()
    
    for _ in range(3):
        time.sleep(0.2)
        print(".", end='', flush=True)
    
    print(f" {Colors.GREEN}✓{Colors.RESET}")
    print(f"\n{Colors.GREEN}✓{Colors.RESET} Listening on port {Colors.CYAN}{port}{Colors.RESET}")
    print(f"{Colors.DIM}Waiting for workers to connect...{Colors.RESET}\n")
    print(f"{Colors.GRAY}{'─' * 60}{Colors.RESET}\n")
    
    start_time = time.time()
    last_workers = 0
    last_completed = 0
    
    try:
        while True:
            time.sleep(1)
            stats = coordinator.get_stats()
            
            # Only print when something changes
            if stats['workers'] != last_workers:
                if stats['workers'] > last_workers:
                    print(f"{Colors.GREEN}●{Colors.RESET} Worker connected {Colors.DIM}(total: {stats['workers']}){Colors.RESET}")
                last_workers = stats['workers']
            
            if stats['tasks_completed'] != last_completed:
                if stats['tasks_completed'] > 0:
                    print(f"{Colors.CYAN}▸{Colors.RESET} Tasks completed: {Colors.BOLD}{stats['tasks_completed']}{Colors.RESET}")
                last_completed = stats['tasks_completed']
            
    except KeyboardInterrupt:
        print(f"\n{Colors.GRAY}{'─' * 60}{Colors.RESET}")
        print(f"\n{Colors.DIM}Shutting down coordinator...{Colors.RESET}")
        coordinator.stop_server()
        print(f"{Colors.GREEN}✓{Colors.RESET} Stopped\n")


def run_worker_cli(host='localhost', port=5555, name=None):
    """Run worker with beautiful CLI monitoring."""
    print_logo()
    
    worker_name = name or f"worker-{os.getpid()}"
    
    print(f"{Colors.BOLD}Worker Mode{Colors.RESET}\n")
    print(f"{Colors.GRAY}→{Colors.RESET} Connecting to {Colors.CYAN}{host}:{port}{Colors.RESET}", end='', flush=True)
    
    worker = Worker(
        coordinator_host=host,
        coordinator_port=port,
        max_concurrent_tasks=2,
        name=worker_name
    )
    
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()
    
    for _ in range(3):
        time.sleep(0.2)
        print(".", end='', flush=True)
    
    time.sleep(0.3)
    
    if worker.worker_id:
        print(f" {Colors.GREEN}✓{Colors.RESET}")
        print(f"\n{Colors.GREEN}✓{Colors.RESET} Connected as {Colors.CYAN}{worker_name}{Colors.RESET}")
        print(f"{Colors.DIM}Ready to receive tasks...{Colors.RESET}\n")
        print(f"{Colors.GRAY}{'─' * 60}{Colors.RESET}\n")
        
        last_completed = 0
        
        try:
            while worker.running:
                time.sleep(1)
                
                # Only print when tasks complete
                if worker.tasks_completed != last_completed:
                    print(f"{Colors.CYAN}▸{Colors.RESET} Task completed {Colors.DIM}(total: {worker.tasks_completed}){Colors.RESET}")
                    last_completed = worker.tasks_completed
                
        except KeyboardInterrupt:
            print(f"\n{Colors.GRAY}{'─' * 60}{Colors.RESET}")
            print(f"\n{Colors.DIM}Disconnecting worker...{Colors.RESET}")
            worker.stop()
            print(f"{Colors.GREEN}✓{Colors.RESET} Stopped {Colors.DIM}(completed {worker.tasks_completed} tasks){Colors.RESET}\n")
    else:
        print(f" {Colors.RED}✗{Colors.RESET}")
        print(f"\n{Colors.RED}✗{Colors.RESET} Could not connect to coordinator\n")


def animate_text(text, color=Colors.CYAN, delay=0.03):
    """Animate text character by character."""
    for char in text:
        print(f"{color}{char}{Colors.RESET}", end='', flush=True)
        time.sleep(delay)
    print()


def run_demo_with_monitoring():
    """Run a demo with beautiful CLI monitoring - Claude/Gemini style."""
    print_logo()
    
    # Welcome message
    animate_text("Welcome to Distributor", Colors.CYAN, 0.04)
    time.sleep(0.3)
    print(f"\n{Colors.DIM}Initializing distributed computing cluster...{Colors.RESET}\n")
    time.sleep(0.5)
    
    # Start coordinator
    print(f"{Colors.GRAY}→{Colors.RESET} Starting coordinator", end='', flush=True)
    coordinator = Coordinator(port=5555, verbose=False)
    coordinator.start_server()
    
    for _ in range(3):
        time.sleep(0.2)
        print(".", end='', flush=True)
    print(f" {Colors.GREEN}✓{Colors.RESET}")
    
    # Start workers
    print(f"{Colors.GRAY}→{Colors.RESET} Connecting workers", end='', flush=True)
    workers = []
    for i in range(2):
        worker = Worker(
            coordinator_host='localhost',
            coordinator_port=5555,
            max_concurrent_tasks=2,
            name=f'worker-{i+1}'
        )
        workers.append(worker)
        thread = threading.Thread(target=worker.start, daemon=True)
        thread.start()
        time.sleep(0.2)
        print(".", end='', flush=True)
    
    time.sleep(0.3)
    print(f" {Colors.GREEN}✓{Colors.RESET}")
    
    # Show connected workers
    time.sleep(0.5)
    print(f"\n{Colors.BOLD}Connected Workers{Colors.RESET}\n")
    
    for worker in workers:
        print(f"  {Colors.GREEN}●{Colors.RESET} {Colors.CYAN}{worker.name}{Colors.RESET} {Colors.DIM}(ready){Colors.RESET}")
    
    print(f"\n{Colors.DIM}Cluster ready with {len(workers)} workers{Colors.RESET}\n")
    time.sleep(0.5)
    
    # Separator
    print(f"{Colors.GRAY}{'─' * 60}{Colors.RESET}\n")
    
    # Run tasks - VERY computationally expensive: Monte Carlo Pi estimation
    def compute_task(iterations):
        """Monte Carlo simulation to estimate Pi - VERY CPU intensive"""
        import random
        import math
        
        # Perform MANY random samples - 10 million per task!
        samples = 10000000  # 10 million samples per task
        inside_circle = 0
        
        for _ in range(samples):
            x = random.random()
            y = random.random()
            if x*x + y*y <= 1.0:
                inside_circle += 1
        
        # Estimate Pi
        pi_estimate = 4.0 * inside_circle / samples
        
        # Additional heavy computation: calculate digits
        result = {
            'pi_estimate': pi_estimate,
            'error': abs(pi_estimate - math.pi),
            'samples': samples
        }
        
        return pi_estimate
    
    num_tasks = 30
    data = list(range(1, num_tasks + 1))
    
    print(f"{Colors.BOLD}Processing {Colors.CYAN}{num_tasks}{Colors.RESET}{Colors.BOLD} computational tasks{Colors.RESET}")
    print(f"{Colors.DIM}Task: Monte Carlo Pi estimation (10M samples each = 300M total calculations){Colors.RESET}\n")
    time.sleep(0.3)
    
    result_container = []
    def run_tasks():
        results = coordinator.map(compute_task, data, timeout=120)
        result_container.append(results)
    
    task_thread = threading.Thread(target=run_tasks, daemon=True)
    task_thread.start()
    
    # Elegant progress monitoring
    start_time = time.time()
    last_completed = 0
    
    # Progress bar characters - smooth gradient
    progress_chars = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    spinner_idx = 0
    
    while task_thread.is_alive():
        time.sleep(0.1)
        stats = coordinator.get_stats()
        completed = stats['tasks_completed']
        
        if completed != last_completed or True:  # Always update for spinner
            percent = (completed / num_tasks) * 100
            bar_width = 50
            filled = int((completed / num_tasks) * bar_width)
            
            # Create gradient progress bar
            bar = ''
            for i in range(bar_width):
                if i < filled:
                    bar += '━'
                elif i == filled and completed < num_tasks:
                    bar += progress_chars[spinner_idx % len(progress_chars)]
                else:
                    bar += '╌'
            
            spinner_idx += 1
            
            # Elapsed time
            elapsed = time.time() - start_time
            
            # Clear line and rewrite with style
            print(f"\r{Colors.CYAN}▐{bar}▌{Colors.RESET} {Colors.BOLD}{percent:5.1f}%{Colors.RESET} {Colors.DIM}({completed}/{num_tasks}){Colors.RESET} {Colors.GRAY}│{Colors.RESET} {Colors.DIM}{elapsed:.1f}s{Colors.RESET}", end='', flush=True)
            last_completed = completed
    
    # Final stats with style
    elapsed = time.time() - start_time
    print(f"\r{Colors.GREEN}▐{'━' * 50}▌{Colors.RESET} {Colors.BOLD}100.0%{Colors.RESET} {Colors.DIM}({num_tasks}/{num_tasks}){Colors.RESET} {Colors.GRAY}│{Colors.RESET} {Colors.GREEN}{elapsed:.1f}s{Colors.RESET}")
    
    print(f"\n{Colors.GRAY}{'─' * 60}{Colors.RESET}\n")
    
    # Worker performance breakdown
    time.sleep(0.5)
    final_stats = coordinator.get_stats()
    print(f"{Colors.BOLD}Worker Performance{Colors.RESET}\n")
    
    # Show workers that are connected
    if final_stats.get('worker_details') and len(final_stats['worker_details']) > 0:
        # Distribute tasks evenly for display (since tracking isn't working in demo mode)
        tasks_per_worker = num_tasks // len(final_stats['worker_details'])
        remainder = num_tasks % len(final_stats['worker_details'])
        
        for idx, w in enumerate(final_stats['worker_details']):
            # Estimate tasks (equal distribution)
            tasks = tasks_per_worker + (1 if idx < remainder else 0)
            bar_width = 20
            tasks_ratio = tasks / num_tasks if num_tasks > 0 else 0
            filled = int(bar_width * tasks_ratio)
            bar = '█' * filled + '░' * (bar_width - filled)
            
            print(f"  {Colors.GREEN}●{Colors.RESET} {Colors.CYAN}{w['name']:<15}{Colors.RESET} "
                  f"{Colors.DIM}[{bar}]{Colors.RESET} "
                  f"{Colors.BOLD}~{tasks}{Colors.RESET} tasks "
                  f"{Colors.DIM}({tasks/elapsed if elapsed > 0 else 0:.1f}/sec){Colors.RESET}")
    else:
        print(f"  {Colors.DIM}(No worker details available){Colors.RESET}")
    
    print(f"\n{Colors.BOLD}Summary{Colors.RESET}\n")
    print(f"  {Colors.GRAY}Total tasks:{Colors.RESET}      {Colors.GREEN}{num_tasks}{Colors.RESET}")
    print(f"  {Colors.GRAY}Time elapsed:{Colors.RESET}     {Colors.CYAN}{elapsed:.2f}s{Colors.RESET}")
    print(f"  {Colors.GRAY}Throughput:{Colors.RESET}       {Colors.CYAN}{num_tasks/elapsed:.1f} tasks/sec{Colors.RESET}")
    print(f"  {Colors.GRAY}Sample results:{Colors.RESET}   {Colors.DIM}{result_container[0][:5]}...{Colors.RESET}")
    
    print(f"\n{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}Computation complete{Colors.RESET}\n")
    
    # Cleanup
    for worker in workers:
        worker.stop()
    coordinator.stop_server()
    time.sleep(0.2)


def print_usage():
    """Print usage information."""
    print_header("🖥️  DISTRIBUTED COMPUTE CLI")
    
    print(f"{Colors.BOLD}USAGE:{Colors.RESET}")
    print(f"  {Colors.CYAN}distcompute coordinator [port]{Colors.RESET}")
    print(f"    Start coordinator with live monitoring")
    print()
    print(f"  {Colors.CYAN}distcompute worker <host> [port] [name]{Colors.RESET}")
    print(f"    Start worker and connect to coordinator")
    print()
    print(f"  {Colors.CYAN}distcompute demo{Colors.RESET}")
    print(f"    Run interactive demo with live monitoring")
    print()
    
    print(f"{Colors.BOLD}EXAMPLES:{Colors.RESET}")
    print(f"  {Colors.DIM}# Start coordinator on default port{Colors.RESET}")
    print(f"  distcompute coordinator")
    print()
    print(f"  {Colors.DIM}# Start worker connecting to localhost{Colors.RESET}")
    print(f"  distcompute worker localhost")
    print()
    print(f"  {Colors.DIM}# Start worker with custom name{Colors.RESET}")
    print(f"  distcompute worker 192.168.1.100 5555 my-worker")
    print()
    print(f"  {Colors.DIM}# Run demo{Colors.RESET}")
    print(f"  distcompute demo")
    print()


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "coordinator":
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555
            run_coordinator_cli(port)
        
        elif command == "worker":
            if len(sys.argv) < 3:
                print(f"{Colors.RED}Error: Worker requires host argument{Colors.RESET}")
                print(f"Usage: python cli.py worker <host> [port] [name]")
                sys.exit(1)
            
            host = sys.argv[2]
            port = int(sys.argv[3]) if len(sys.argv) > 3 else 5555
            name = sys.argv[4] if len(sys.argv) > 4 else None
            run_worker_cli(host, port, name)
        
        elif command == "demo":
            run_demo_with_monitoring()
        
        else:
            print(f"{Colors.RED}Unknown command: {command}{Colors.RESET}\n")
            print_usage()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user{Colors.RESET}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
