#!/usr/bin/env python3
"""
Setup Verification Script for Agent Template

This script checks that your environment is properly configured
for agent development.
"""

import os
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def check_python_version():
    """Check Python version is 3.11+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (Need 3.11+)"


def check_environment_variables():
    """Check required environment variables"""
    required = ["OPENAI_API_KEY"]
    missing = []

    for var in required:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        return False, f"Missing: {', '.join(missing)}"
    return True, "All required environment variables set"


def check_imports():
    """Check that key imports work"""
    try:
        # Add src to path for imports
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

        import openai  # noqa: F401

        from src.agent_project.application.services import AgentService  # noqa: F401
        from src.agent_project.domain.entities import Agent  # noqa: F401

        return True, "All imports successful"
    except ImportError as e:
        return False, f"Import error: {str(e)}"


def check_jupyter_kernel():
    """Check Jupyter kernel is installed"""
    try:
        result = subprocess.run(["jupyter", "kernelspec", "list"], capture_output=True, text=True, check=True)
        if "agent-template" in result.stdout:
            return True, "Agent Template kernel installed"
        return False, "Agent Template kernel not found"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, "Jupyter not available or kernel not installed"


def run_basic_test():
    """Run a basic functionality test"""
    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

        from src.agent_project.domain.entities import Agent

        # Create a test agent
        agent = Agent.create_assistant(name="Test Agent", system_prompt="You are a test assistant.")

        if agent.is_configured:
            return True, "Basic agent creation works"
        return False, "Agent creation failed validation"

    except Exception as e:
        return False, f"Test failed: {str(e)}"


def main():
    """Run all verification checks"""
    console.print(
        Panel(
            "[bold blue]🚀 Agent Template Setup Verification[/bold blue]\n\n"
            "Checking your environment configuration...",
            title="Setup Verification",
            border_style="blue",
        )
    )

    checks = [
        ("Python Version", check_python_version),
        ("Environment Variables", check_environment_variables),
        ("Package Imports", check_imports),
        ("Jupyter Kernel", check_jupyter_kernel),
        ("Basic Functionality", run_basic_test),
    ]

    table = Table(title="🔍 Verification Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")

    all_passed = True

    for check_name, check_func in checks:
        try:
            success, message = check_func()
            status = "✅ PASS" if success else "❌ FAIL"
            style = "green" if success else "red"

            table.add_row(check_name, f"[{style}]{status}[/{style}]", message)

            if not success:
                all_passed = False

        except Exception as e:
            table.add_row(check_name, "[red]❌ ERROR[/red]", f"Exception: {str(e)}")
            all_passed = False

    console.print(table)
    console.print()

    if all_passed:
        console.print(
            Panel(
                "[bold green]🎉 All checks passed![/bold green]\n\n"
                "Your agent template is ready to use:\n"
                "• Try: [cyan]python tools/agent_cli.py interactive[/cyan]\n"
                "• Or open: [cyan]notebooks/01_basic_agent_example.ipynb[/cyan]\n"
                "• API docs: [cyan]python apps/main.py[/cyan] then visit http://localhost:8000/docs",
                title="✅ Setup Complete",
                border_style="green",
            )
        )
        return 0
    else:
        console.print(
            Panel(
                "[bold red]❌ Some checks failed[/bold red]\n\n"
                "Please review the SETUP.md guide:\n"
                "• Check Python version (need 3.11+)\n"
                "• Set OPENAI_API_KEY environment variable\n"
                "• Run: [cyan]poetry install[/cyan]\n"
                "• Install kernel: [cyan]python -m ipykernel install --user --name agent-template[/cyan]",
                title="⚠️ Setup Issues",
                border_style="red",
            )
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
