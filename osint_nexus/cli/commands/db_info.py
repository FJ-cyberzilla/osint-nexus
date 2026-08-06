import argparse
from typing import Any

from osint_nexus.utils.troubleshoot import (
    inspect_database_schema,
    print_latest_scan_results,
)


def handle_db_info_command(args: argparse.Namespace) -> None:
    """Inspect database schema and records."""
    inspect_database_schema()
    print_latest_scan_results()


def setup_db_info_parser(subparsers: Any) -> None:
    """Configure the db-info command parser."""
    subparsers.add_parser("db-info", help="Inspect database schema and records")
