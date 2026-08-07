from typing import TYPE_CHECKING

import argparse

from osint_nexus.utils.troubleshoot import (
    inspect_database_schema,
    print_latest_scan_results,
)

if TYPE_CHECKING:
    from argparse import _SubParsersAction, ArgumentParser


def handle_db_info_command(args: argparse.Namespace) -> None:
    """Inspect database schema and records."""
    inspect_database_schema()
    print_latest_scan_results()


def setup_db_info_parser(subparsers: "_SubParsersAction[ArgumentParser]") -> None:
    """Configure the db-info command parser."""
    subparsers.add_parser("db-info", help="Inspect database schema and records")
