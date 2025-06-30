#!/usr/bin/env python3
"""
Unified service stop script.

This script stops all services using the service manager for coordinated shutdown.
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path for utils
sys.path.insert(0, str(Path(__file__).parent))

from utils.service_manager import ServiceManager


def main():
    """Main entry point for service shutdown."""
    parser = argparse.ArgumentParser(
        description="Stop agent template services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/stop_services.py --mode=development
  python scripts/stop_services.py --mode=production
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["development", "production", "testing"],
        default="development",
        help="Environment mode (default: development)",
    )

    args = parser.parse_args()

    try:
        # Create service manager
        manager = ServiceManager(mode=args.mode)

        # Stop all services
        manager.stop_services()

        print("✅ All services have been stopped")
        sys.exit(0)

    except Exception as e:
        print(f"❌ Error stopping services: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
