"""
Command Line Interface entry point for OSINT Nexus.
"""

from __future__ import annotations

import argparse

from rich.console import Console

from osint_nexus.cli.commands.db_info import handle_db_info_command, setup_db_info_parser
from osint_nexus.cli.commands.health import handle_health_command, setup_health_parser
from osint_nexus.cli.commands.scan import handle_scan_command, setup_scan_parser
from osint_nexus.utils.troubleshoot import setup_logging

console = Console()


def main() -> None:
    """Synchronous entry point that safely wraps the asyncio loop."""
    parser = argparse.ArgumentParser(description="Advanced OSINT Target Scanner")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)

    # Setup modular commands
    setup_scan_parser(subparsers)
    setup_health_parser(subparsers)
    setup_db_info_parser(subparsers)

    args = parser.parse_args()

    setup_logging(verbose=args.debug)

    # Command handling
    if args.command == "scan":
        handle_scan_command(args)
    elif args.command == "health":
        handle_health_command(args)
    elif args.command == "db-info":
        handle_db_info_command(args)


if __name__ == "__main__":
    main()
