#!/usr/bin/env python3
"""
Unified service startup script.

This script starts all services using centralized configuration from settings.
No manual environment variable exports needed - everything comes from settings.
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path for utils
sys.path.insert(0, str(Path(__file__).parent))

from utils.service_manager import ServiceManager


def main():
    """Main entry point for service startup."""
    parser = argparse.ArgumentParser(
        description="Start agent template services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/start_services.py --mode=development
  python scripts/start_services.py --mode=production
  python scripts/start_services.py --mode=testing
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["development", "production", "testing"],
        default="development",
        help="Environment mode to run in (default: development)",
    )

    args = parser.parse_args()

    try:
        # Create service manager
        manager = ServiceManager(mode=args.mode)

        # Start services
        success = manager.start_services()

        if success:
            print("\n💡 To stop services, run: make dev-stop")
            print("💡 To check status, run: make dev-status")

            # In development mode, run interactively
            if args.mode == "development":
                try:
                    print("\n🔄 Services running. Press Ctrl+C to stop...")
                    while True:
                        import time

                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Stopping services...")
                    manager.stop_services()

            sys.exit(0)
        else:
            print("❌ Failed to start services")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Interrupted, stopping services...")
        if "manager" in locals():
            manager.stop_services()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
