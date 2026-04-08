import json
from pathlib import Path
from unittest.mock import patch

import pytest

from pliparser import run_plip2csv
from pliparser.core import read_json_config
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


def test_read_json_config_parses_valid_json(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.json"
    config_data = {
        "pdb": "protein.pdb",
        "model_id": 1,
        "receptor_chain": "A",
        "ligand_chain": "B",
        "transparency": 65,
        "issmalmol": False,
        "receptor_color": "gray",
        "ligand_color": "green",
    }
    cfg_file.write_text(json.dumps(config_data), encoding="UTF-8")

    result = read_json_config(cfg_file)

    assert result == config_data


def test_read_json_config_raises_on_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "nonexistent.json"

    with pytest.raises(FileNotFoundError):
        read_json_config(missing_file)


def test_read_json_config_raises_on_invalid_json(tmp_path: Path) -> None:
    bad_json_file = tmp_path / "bad.json"
    bad_json_file.write_text("{ invalid json }", encoding="UTF-8")

    with pytest.raises(json.JSONDecodeError):
        read_json_config(bad_json_file)


@patch("pliparser.core.read_json_config")
@patch("pliparser.core.write_cxc_file")
def test_run_csv2cxc_with_config_path_takes_precedence(mock_write_cxc_file, mock_read_json_config):
    mock_read_json_config.return_value = {"model_id": 1, "source": "json"}

    cfg_dict = {"model_id": 2, "source": "dict"}

    run_csv2cxc_with_config("csv_dir", "out.cxc", config=cfg_dict, config_path="cfg.json")

    mock_read_json_config.assert_called_once()
    # Verify that read_json_config result was used, not the config dict
    call_args = mock_write_cxc_file.call_args
    assert call_args[0][2] == {"model_id": 1, "source": "json"}


@patch("pliparser.core.plip2csv_stream")
def test_run_plip2csv_converts_to_path_objects(mock_plip2csv_stream):
    run_plip2csv("input.txt", "output_dir")

    mock_plip2csv_stream.assert_called_once()
    call_args = mock_plip2csv_stream.call_args[0]
    assert isinstance(call_args[0], Path)
    assert isinstance(call_args[1], Path)
    assert call_args[0] == Path("input.txt")
    assert call_args[1] == Path("output_dir")
