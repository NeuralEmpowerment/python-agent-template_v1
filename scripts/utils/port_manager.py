"""
Port management utilities for service startup.
"""

import socket
import subprocess
from typing import List


def is_port_available(port: int, host: str = "localhost") -> bool:
    """
    Check if a port is available for binding.

    Args:
        port: Port number to check
        host: Host to check on

    Returns:
        bool: True if port is available, False if in use
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0  # Port is available if connection fails
    except Exception:
        return False


def find_processes_on_port(port: int) -> List[str]:
    """
    Find processes running on a specific port.

    Args:
        port: Port number to check

    Returns:
        List[str]: List of process descriptions
    """
    try:
        # Use lsof to find processes on the port
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=5)

        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            processes = []

            for pid in pids:
                try:
                    ps_result = subprocess.run(
                        ["ps", "-p", pid, "-o", "pid,comm"], capture_output=True, text=True, timeout=5
                    )
                    if ps_result.returncode == 0:
                        lines = ps_result.stdout.strip().split("\n")
                        if len(lines) > 1:  # Skip header
                            processes.append(lines[1].strip())
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    processes.append(f"PID {pid} (unknown)")

            return processes
        return []

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return []


def kill_processes_on_port(port: int, signal: str = "TERM") -> bool:
    """
    Kill processes running on a specific port.

    Args:
        port: Port number to clear
        signal: Signal to send (TERM, KILL, etc.)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Find processes on the port
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=5)

        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split("\n")

            for pid in pids:
                try:
                    subprocess.run(["kill", f"-{signal}", pid], timeout=5, check=True)
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    continue

            return True
        return True  # No processes to kill

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return False


def get_service_port_info() -> dict:
    """
    Get information about standard service ports.

    Returns:
        dict: Port information for each service
    """
    return {
        "fastapi": {
            "port": 8000,
            "name": "Agent Template API",
            "url": "http://localhost:8000",
            "health_check": "http://localhost:8000/health",
        }
    }
