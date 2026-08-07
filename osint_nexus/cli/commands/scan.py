from typing import TYPE_CHECKING

import argparse
import asyncio
import logging

from rich.console import Console

from osint_nexus.cli.scanner import run_scan
from osint_nexus.core.agent import OSINTAgent
from osint_nexus.utils.security import SecurityUtility

console = Console()

if TYPE_CHECKING:
    from argparse import _SubParsersAction

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
        from osint_nexus.cli.scanner import generate_report

        await generate_report(agent)
        console.print("\n[bold green]Scan completed successfully![/]")
        console.print("[bold green]Reconnaissance finished.[/]")


def handle_scan_command(args: argparse.Namespace) -> None:
    """Execute the scan command."""
    asyncio.run(async_main(args))


def setup_scan_parser(subparsers: "_SubParsersAction") -> None:
    """Configure the scan command parser."""
    scan_parser = subparsers.add_parser("scan", help="Scan a target username")
    scan_parser.add_argument("--username", required=True, help="Target username to investigate")
    scan_parser.add_argument("--timeout", type=float, default=15.0, help="Per-provider timeout in seconds")
