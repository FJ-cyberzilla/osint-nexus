from typing import TYPE_CHECKING

import argparse
from rich.console import Console

from osint_nexus.utils.troubleshoot import run_health_check

console = Console()

if TYPE_CHECKING:
    from argparse import _SubParsersAction, ArgumentParser


def handle_health_command(args: argparse.Namespace) -> None:
    """Check provider health status."""
    run_health_check()


def setup_health_parser(subparsers: "_SubParsersAction[ArgumentParser]") -> None:
    """Configure the health command parser."""
    subparsers.add_parser("health", help="Check provider health status")
