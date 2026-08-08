import unittest
from unittest.mock import MagicMock, patch

from osint_nexus.cli.main import main


class TestCLIMain(unittest.TestCase):
    @patch("osint_nexus.cli.main.argparse.ArgumentParser.parse_args")
    @patch("osint_nexus.cli.main.handle_scan_command")
    @patch("osint_nexus.cli.main.setup_logging")
    def test_main_scan(self, mock_logging, mock_handle_scan, mock_parse_args):
        # Setup mock args
        args = MagicMock()
        args.command = "scan"
        args.debug = False
        mock_parse_args.return_value = args

        main()

        mock_handle_scan.assert_called_once_with(args)

    @patch("osint_nexus.cli.main.argparse.ArgumentParser.parse_args")
    @patch("osint_nexus.cli.main.handle_health_command")
    @patch("osint_nexus.cli.main.setup_logging")
    def test_main_health(self, mock_logging, mock_handle_health, mock_parse_args):
        # Setup mock args
        args = MagicMock()
        args.command = "health"
        args.debug = False
        mock_parse_args.return_value = args

        main()

        mock_handle_health.assert_called_once_with(args)

    @patch("osint_nexus.cli.main.argparse.ArgumentParser.parse_args")
    @patch("osint_nexus.cli.main.handle_db_info_command")
    @patch("osint_nexus.cli.main.setup_logging")
    def test_main_db_info(self, mock_logging, mock_handle_db_info, mock_parse_args):
        # Setup mock args
        args = MagicMock()
        args.command = "db-info"
        args.debug = False
        mock_parse_args.return_value = args

        main()

        mock_handle_db_info.assert_called_once_with(args)
