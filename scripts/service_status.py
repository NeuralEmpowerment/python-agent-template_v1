#!/usr/bin/env python3
"""
Service status checker script.

This script checks and displays the status of all application services.
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path for utils
sys.path.insert(0, str(Path(__file__).parent))

from utils.service_manager import ServiceManager


def main():
    """Main entry point for service status checking."""
    parser = argparse.ArgumentParser(
        description="Check status of agent template services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/service_status.py --mode=development
  python scripts/service_status.py --mode=production
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["development", "production", "testing"],
        default="development",
        help="Environment mode (default: development)",
    )

    parser.add_argument("--json", action="store_true", help="Output status in JSON format")

    args = parser.parse_args()

    try:
        # Create service manager
        manager = ServiceManager(mode=args.mode)

        # Get service status
        status = manager.get_service_status()

        if args.json:
            import json

            print(json.dumps(status, indent=2))
        else:
            print(f"📊 Service Status ({args.mode} mode)")
            print("=" * 50)

            all_running = True

            for service_name, info in status.items():
                if info["running"]:
                    health_status = ""
                    if info["health_check"] is not None:
                        health_status = " ✅" if info["health_check"] else " ⚠️"
                    print(f"✅ {info['name']}: Running on port {info['port']}{health_status}")
                    print(f"   URL: {info['url']}")
                else:
                    print(f"❌ {info['name']}: Not running (port {info['port']} available)")
                    all_running = False

                print()

            if all_running:
                print("🎉 All services are running!")
            else:
                print("⚠️  Some services are not running.")
                print("💡 Run 'make dev-start' to start services")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error checking service status: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
