from unittest.mock import patch

import pytest

from pliparser import run_plip2csv
from pliparser.core import run_csv2cxc
from pliparser.core import run_csv2cxc_with_config


@patch("pliparser.core.plip2csv_stream")
def test_run_plip2csv_calls_stream(mock_plip2csv_stream):
    run_plip2csv("report.txt", "out")
    mock_plip2csv_stream.assert_called_once()


@patch("pliparser.core.read_json_config")
@patch("pliparser.core.write_cxc_file")
def test_run_csv2cxc_with_json_path(mock_write_cxc_file, mock_read_json_config):
    mock_read_json_config.return_value = {"model_id": 1}

    run_csv2cxc("csv_dir", "out.cxc", "cfg.json")

    mock_read_json_config.assert_called_once()
    mock_write_cxc_file.assert_called_once()


@patch("pliparser.core.write_cxc_file")
def test_run_csv2cxc_with_explicit_config(mock_write_cxc_file):
    cfg = {
        "pdb": "protein.pdb",
        "model_id": 1,
        "receptor_chain": "A",
        "ligand_chain": "B",
        "transparency": 65,
        "issmalmol": True,
        "receptor_color": "gray",
        "ligand_color": "green",
    }

    run_csv2cxc_with_config("csv_dir", "out.cxc", config=cfg)

    mock_write_cxc_file.assert_called_once()


def test_run_csv2cxc_with_config_requires_source():
    with pytest.raises(ValueError, match="Either 'config_path' or 'config' must be provided"):
        run_csv2cxc_with_config("csv_dir", "out.cxc")
