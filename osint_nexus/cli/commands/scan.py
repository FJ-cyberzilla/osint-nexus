import argparse
import asyncio
import logging
from typing import Any

from rich.console import Console

from osint_nexus.cli.scanner import run_scan
from osint_nexus.core.agent import OSINTAgent
from osint_nexus.utils.security import SecurityUtility

console = Console()


async def async_main(args: argparse.Namespace) -> None:
    """Main async entry point for the scan CLI."""
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    safe_username = SecurityUtility.sanitize_input(args.username)
    agent = OSINTAgent(safe_username)

    try:
        await run_scan(agent, safe_username, args.timeout)
    except asyncio.CancelledError:
        console.print("[yellow]Scan cancelled by system.[/]")
        raise
    finally:
        # Assuming generate_report is moved or kept in cli/main.py
        # For now, importing from a shared place or re-implementing if needed.
        # As per plan, let's keep generate_report simple or move it too.
        # Given I don't want to break too much, I'll keep it in main.py for now
        # and re-import it here if necessary.
        from osint_nexus.cli.main import generate_report

        generate_report(agent)


def handle_scan_command(args: argparse.Namespace) -> None:
    """Execute the scan command."""
    asyncio.run(async_main(args))


def setup_scan_parser(subparsers: Any) -> None:
    """Configure the scan command parser."""
    scan_parser = subparsers.add_parser("scan", help="Scan a target username")
    scan_parser.add_argument("--username", required=True, help="Target username to investigate")
    scan_parser.add_argument("--timeout", type=float, default=15.0, help="Per-provider timeout in seconds")
