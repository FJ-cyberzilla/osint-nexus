"""
Command Line Interface entry point for OSINT Nexus.
"""

from __future__ import annotations

import argparse
from typing import Self

from beartype import beartype
from rich.console import Console

from osint_nexus.cli.commands.db_info import handle_db_info_command, setup_db_info_parser
from osint_nexus.cli.commands.health import handle_health_command, setup_health_parser
from osint_nexus.cli.commands.scan import handle_scan_command, setup_scan_parser
from osint_nexus.utils.troubleshoot import setup_logging

console: Console = Console()


@beartype
class CLIConfig:
    """Zero-comma parameter container for main CLI arguments."""

    def __init__(self: Self) -> None:
        self.args: argparse.Namespace

    def set_args(self: Self, args: argparse.Namespace) -> Self:
        self.args = args
        return self


@beartype
def execute_command(config: CLIConfig) -> None:
    """Dispatches CLI commands without multi-parameter comma signatures."""
    args: argparse.Namespace = config.args
    command: str | None = args.command

    if command == "scan":
        handle_scan_command(args=args)
    elif command == "health":
        handle_health_command(args=args)
    elif command == "db-info":
        handle_db_info_command(args=args)


@beartype
def main() -> None:
    """Synchronous entry point that safely wraps the asyncio loop."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Advanced OSINT Target Scanner")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    subparsers: argparse._SubParsersAction[argparse.ArgumentParser] = parser.add_subparsers(
        dest="command", help="Command to run", required=True
    )

    setup_scan_parser(subparsers=subparsers)
    setup_health_parser(subparsers=subparsers)
    setup_db_info_parser(subparsers=subparsers)

    parsed_args: argparse.Namespace = parser.parse_args()

    setup_logging(verbose=parsed_args.debug)

    config: CLIConfig = CLIConfig().set_args(args=parsed_args)
    execute_command(config=config)


if __name__ == "__main__":
    main()
