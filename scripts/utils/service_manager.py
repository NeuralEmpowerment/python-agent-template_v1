"""
Service management utilities for agent template coordinated startup/shutdown.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict

import requests

# Add project root to path for importing settings
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import project modules after path setup
from scripts.utils.port_manager import (  # noqa: E402
    find_processes_on_port,
    get_service_port_info,
    is_port_available,
    kill_processes_on_port,
)
from src.agent_project.config.settings import get_settings  # noqa: E402


class ServiceManager:
    """Manages agent template services with centralized configuration."""

    def __init__(self, mode: str = "development"):
        """
        Initialize service manager.

        Args:
            mode: Environment mode (development, production, testing)
        """
        self.mode = mode
        self.settings = get_settings()
        self.settings.api.environment = mode
        self.port_info = get_service_port_info()
        self.processes: Dict[str, subprocess.Popen] = {}

    def _set_environment_variables(self) -> None:
        """Set required environment variables based on centralized settings."""
        # macOS multiprocessing fix
        if self.settings.objc_disable_initialize_fork_safety:
            os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

    def _validate_settings(self) -> None:
        """Validate settings and environment before starting services."""
        try:
            self.settings.validate_configuration()
            print("✅ Configuration validation passed")
        except ValueError as e:
            print(f"❌ Configuration validation failed: {e}")
            raise

    def _cleanup_existing_services(self) -> None:
        """Clean up any existing services on required ports."""
        print("🧹 Cleaning up any existing services...")

        for service_name, info in self.port_info.items():
            port = info["port"]
            processes = find_processes_on_port(port)

            if processes:
                print(f"   Stopping existing {info['name']} processes on port {port}")
                kill_processes_on_port(port, "TERM")
                time.sleep(1)

                # Force kill if still running
                if not is_port_available(port):
                    print(f"   Force stopping processes on port {port}")
                    kill_processes_on_port(port, "KILL")
                    time.sleep(1)

        print("✅ Service cleanup completed")

    def _wait_for_service(self, service_name: str, timeout: int = 30) -> bool:
        """
        Wait for a service to become available.

        Args:
            service_name: Name of the service to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if service is available, False if timeout
        """
        if service_name not in self.port_info:
            return False

        info = self.port_info[service_name]
        health_url = info.get("health_check", info["url"])

        print(f"   Waiting for {info['name']} to start...")

        for i in range(timeout):
            try:
                response = requests.get(health_url, timeout=2)
                if response.status_code == 200:
                    print(f"   ✅ {info['name']} is ready at {info['url']}")
                    return True
            except requests.RequestException:
                pass

            time.sleep(1)

        print(f"   ❌ {info['name']} failed to start within {timeout} seconds")
        return False

    def start_fastapi_server(self) -> bool:
        """
        Start FastAPI server.

        Returns:
            bool: True if started successfully, False otherwise
        """
        if not is_port_available(self.port_info["fastapi"]["port"]):
            print(f"⚠️  Port {self.port_info['fastapi']['port']} is already in use")
            return False

        print("🚀 Starting FastAPI server...")

        try:
            cmd = ["python", "-m", "uvicorn", "apps.main:app", "--port", str(self.port_info["fastapi"]["port"])]

            if self.mode == "development":
                cmd.append("--reload")
            else:
                cmd.extend(["--host", "0.0.0.0"])

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            self.processes["fastapi"] = process

            # Wait for FastAPI to be ready
            if self._wait_for_service("fastapi", timeout=15):
                return True
            else:
                process.terminate()
                return False

        except Exception as e:
            print(f"❌ Failed to start FastAPI server: {e}")
            return False

    def stop_services(self) -> None:
        """Stop all managed services."""
        print("🛑 Stopping services...")

        # Stop managed processes
        for service_name, process in self.processes.items():
            if process and process.poll() is None:
                print(f"   Stopping {service_name}...")
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"   Force killing {service_name}...")
                    process.kill()

        # Clean up ports
        for service_name, info in self.port_info.items():
            port = info["port"]
            if not is_port_available(port):
                print(f"   Cleaning up port {port}...")
                kill_processes_on_port(port, "TERM")

        self.processes.clear()
        print("✅ Services stopped")

    def get_service_status(self) -> Dict[str, dict]:
        """
        Get status of all services.

        Returns:
            Dict[str, dict]: Status information for each service
        """
        status = {}

        for service_name, info in self.port_info.items():
            port = info["port"]
            is_available = is_port_available(port)

            service_status = {
                "name": info["name"],
                "port": port,
                "url": info["url"],
                "running": not is_available,
                "health_check": None,
            }

            if not is_available:
                # Try health check
                try:
                    health_url = info.get("health_check", info["url"])
                    response = requests.get(health_url, timeout=2)
                    service_status["health_check"] = response.status_code == 200
                except requests.RequestException:
                    service_status["health_check"] = False

            status[service_name] = service_status

        return status

    def start_services(self) -> bool:
        """
        Start all services in the correct order.

        Returns:
            bool: True if all services started successfully
        """
        print(f"🚀 Starting services in {self.mode} mode...")

        try:
            # Step 1: Set environment variables
            self._set_environment_variables()

            # Step 2: Validate configuration
            self._validate_settings()

            # Step 3: Clean up existing services
            self._cleanup_existing_services()

            # Step 4: Start FastAPI server
            if not self.start_fastapi_server():
                print("❌ FastAPI server failed to start")
                self.stop_services()
                return False

                # Step 5: Display status
            print("\n🎉 Services started successfully!")
            self._display_service_info()

            return True

        except Exception as e:
            print(f"❌ Failed to start services: {e}")
            self.stop_services()
            return False

    def _display_service_info(self) -> None:
        """Display information about running services."""
        settings_info = self.settings.get_startup_info()

        print("\n" + "=" * 50)
        print("🤖  Agent Template Service")
        print("=" * 50)
        print(f"Environment: {self.mode}")
        print(f"Database: {settings_info['database']['type']} ({settings_info['database']['url']})")
        print(f"Storage: {settings_info['storage']['backend']} ({settings_info['storage']['path']})")
        print(f"OpenAI Configured: {'✅' if settings_info['agents']['openai_configured'] else '❌'}")
        print("\n📊 Service URLs:")

        status = self.get_service_status()
        for service_name, info in status.items():
            if info["running"]:
                health_indicator = "✅" if info["health_check"] else "⚠️"
                print(f"{health_indicator} {info['name']}: {info['url']}")

                # Add specific links for each service
                if service_name == "fastapi":
                    print(f"   • API Documentation: {info['url']}/docs")
                    print(f"   • Redoc Documentation: {info['url']}/redoc")
                    print(f"   • Configuration Status: {info['url']}/config/status")

        print("=" * 50)

        if self.mode == "development":
            print("\n💡 Development Tips:")
            print("   • FastAPI auto-reloads on code changes")
            print("   • Use 'make dev-stop' to stop all services")
            print("   • Use 'make dev-status' to check service health")
