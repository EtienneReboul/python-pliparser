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

    def test_get_arguments_csv2cxc_with_json_only(self):
        """Test parsing csv2cxc with JSON config does not require explicit options."""
        test_args = ["csv2cxc", "--input", "csv_dir", "--output", "out.cxc", "--config", "cfg.json"]
        with patch.object(sys, "argv", ["prog", *test_args]):
            args = get_arguments()
            assert args.subcommand == "csv2cxc"
            assert args.input == "csv_dir"
            assert args.output == "out.cxc"
            assert args.config == "cfg.json"

    def test_get_arguments_csv2cxc_requires_explicit_options_without_json(self):
        """Test csv2cxc errors when neither config JSON nor full explicit options are provided."""
        test_args = ["csv2cxc", "--input", "csv_dir", "--output", "out.cxc"]
        with patch.object(sys, "argv", ["prog", *test_args]):
            with pytest.raises(SystemExit):
                get_arguments()

    def test_get_arguments_csv2cxc_with_explicit_options(self):
        """Test parsing csv2cxc with all explicit options and no JSON config."""
        test_args = [
            "csv2cxc",
            "--input",
            "csv_dir",
            "--output",
            "out.cxc",
            "--pdb",
            "protein.pdb",
            "--model-id",
            "1",
            "--receptor-chain",
            "A",
            "--ligand-chain",
            "B",
            "--transparency",
            "65",
            "--receptor-color",
            "gray",
            "--ligand-color",
            "green",
            "--issmalmol",
        ]
        with patch.object(sys, "argv", ["prog", *test_args]):
            args = get_arguments()
            assert args.subcommand == "csv2cxc"
            assert args.config is None
            assert args.pdb == "protein.pdb"
            assert args.model_id == 1
            assert args.issmalmol is True


class TestRun:
    """Tests for the run function."""

    @patch("pliparser.cli.run_plip2csv")
    def test_run_plip2csv_subcommand(self, mock_run_plip2csv):
        """Test run function with plip2csv subcommand."""
        test_args = ["plip2csv", "--input", "input.txt", "--output", "output_dir"]
        with patch.object(sys, "argv", ["prog", *test_args]):
            run()
            mock_run_plip2csv.assert_called_once_with("input.txt", "output_dir")

    @patch("pliparser.cli.run_csv2cxc_with_config")
    def test_run_csv2cxc_subcommand_with_json(self, mock_run_csv2cxc_with_config):
        """Test run function with csv2cxc subcommand using JSON config."""
        test_args = ["csv2cxc", "--input", "csv_dir", "--output", "out.cxc", "--config", "cfg.json"]
        with patch.object(sys, "argv", ["prog", *test_args]):
            run()
            mock_run_csv2cxc_with_config.assert_called_once_with("csv_dir", "out.cxc", config=None, config_path="cfg.json")

    @patch("pliparser.cli.run_csv2cxc_with_config")
    def test_run_csv2cxc_subcommand_with_explicit_flags(self, mock_run_csv2cxc_with_config):
        """Test run function with csv2cxc explicit options and no JSON config."""
        test_args = [
            "csv2cxc",
            "--input",
            "csv_dir",
            "--output",
            "out.cxc",
            "--pdb",
            "protein.pdb",
            "--model-id",
            "1",
            "--receptor-chain",
            "A",
            "--ligand-chain",
            "B",
            "--transparency",
            "65",
            "--receptor-color",
            "gray",
            "--ligand-color",
            "green",
            "--issmalmol",
        ]
        with patch.object(sys, "argv", ["prog", *test_args]):
            run()
            mock_run_csv2cxc_with_config.assert_called_once()
            args, kwargs = mock_run_csv2cxc_with_config.call_args
            assert args == ("csv_dir", "out.cxc")
            assert kwargs["config_path"] is None
            assert kwargs["config"] == {
                "pdb": "protein.pdb",
                "model_id": 1,
                "receptor_chain": "A",
                "ligand_chain": "B",
                "transparency": 65,
                "issmalmol": True,
                "receptor_color": "gray",
                "ligand_color": "green",
            }

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
