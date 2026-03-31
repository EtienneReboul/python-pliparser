import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from pliparser.cli import get_arguments
from pliparser.cli import run


class TestGetArguments:
    """Tests for the get_arguments function."""

    def test_get_arguments_plip2csv_valid(self):
        """Test parsing valid plip2csv arguments."""
        test_args = ["plip2csv", "--input", "input.txt", "--output", "output_dir"]
        with patch.object(sys, "argv", ["prog", *test_args]):
            args = get_arguments()
            assert args.subcommand == "plip2csv"
            assert args.input == "input.txt"
            assert args.output == "output_dir"

    def test_get_arguments_missing_input(self):
        """Test that missing --input argument raises error."""
        test_args = ["plip2csv", "--output", "output_dir"]
        with patch.object(sys, "argv", ["prog", *test_args]):
            with pytest.raises(SystemExit):
                get_arguments()

    def test_get_arguments_missing_output(self):
        """Test that missing --output argument raises error."""
        test_args = ["plip2csv", "--input", "input.txt"]
        with patch.object(sys, "argv", ["prog", *test_args]):
            with pytest.raises(SystemExit):
                get_arguments()

    def test_get_arguments_missing_subcommand(self):
        """Test that missing subcommand raises error."""
        test_args = []
        with patch.object(sys, "argv", ["prog", *test_args]):
            with pytest.raises(SystemExit):
                get_arguments()


class TestRun:
    """Tests for the run function."""

    @patch("pliparser.cli.run_plip2csv")
    def test_run_plip2csv_subcommand(self, mock_run_plip2csv):
        """Test run function with plip2csv subcommand."""
        test_args = ["plip2csv", "--input", "input.txt", "--output", "output_dir"]
        with patch.object(sys, "argv", ["prog", *test_args]):
            run()
            mock_run_plip2csv.assert_called_once_with("input.txt", "output_dir")

    def test_run_unknown_subcommand(self):
        """Test run function with unknown subcommand raises ValueError."""
        test_args = ["unknown_cmd"]
        with patch.object(sys, "argv", ["prog", *test_args]):
            with pytest.raises(SystemExit):
                run()

    @patch("pliparser.cli.get_arguments")
    def test_run_unknown_subcommand_value_error(self, mock_get_arguments):
        """Test run raises ValueError when parsed subcommand is unknown."""
        mock_get_arguments.return_value = SimpleNamespace(subcommand="unknown_subcommand")

        with pytest.raises(ValueError, match="Unknown subcommand: unknown_subcommand"):
            run()
