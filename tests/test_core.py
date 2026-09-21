import json
from pathlib import Path
from unittest.mock import patch

import pytest

from pliparser import run_plip2csv
from pliparser.core import read_json_config
from pliparser.core import run_csv2cxc_with_config

_MIN_CHAINS = [{"chain": "A", "color": "gray"}]


@patch("pliparser.core.plip2csv_stream")
def test_run_plip2csv_calls_stream(mock_plip2csv_stream):
    run_plip2csv("report.txt", "out")
    mock_plip2csv_stream.assert_called_once()


@patch("pliparser.core.write_cxc_file")
def test_run_csv2cxc_with_explicit_config(mock_write_cxc_file):
    cfg = {
        "pdb": "protein.pdb",
        "model_id": 1,
        "chains": _MIN_CHAINS,
        "sources": [{"name": "main", "input": "csv_dir", "issmalmol": True}],
    }

    run_csv2cxc_with_config("out.cxc", config=cfg)

    mock_write_cxc_file.assert_called_once()


def test_run_csv2cxc_with_config_requires_source():
    with pytest.raises(ValueError, match="Either 'config_path' or 'config' must be provided"):
        run_csv2cxc_with_config("out.cxc")


def test_read_json_config_parses_valid_json(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.json"
    config_data = {
        "pdb": "protein.pdb",
        "model_id": 1,
        "chains": _MIN_CHAINS,
        "sources": [{"name": "main", "input": "csv_dir", "issmalmol": False}],
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
    mock_read_json_config.return_value = {"model_id": 1, "source": "json", "sources": []}

    cfg_dict = {"model_id": 2, "source": "dict"}

    run_csv2cxc_with_config("out.cxc", config=cfg_dict, config_path="cfg.json")

    mock_read_json_config.assert_called_once()
    # Verify that read_json_config result was used, not the config dict
    call_args = mock_write_cxc_file.call_args
    assert call_args[0][1] == {"model_id": 1, "source": "json", "sources": []}


@patch("pliparser.core.write_cxc_file")
def test_run_csv2cxc_with_config_forwards_interaction_types(mock_write_cxc_file):
    cfg = {"model_id": 1, "sources": []}
    interaction_types = {"pi-stacking", "salt_bridge"}

    run_csv2cxc_with_config("out.cxc", config=cfg, interaction_types=interaction_types)

    mock_write_cxc_file.assert_called_once()
    _, kwargs = mock_write_cxc_file.call_args
    assert kwargs["interaction_types"] == interaction_types


@patch("pliparser.core.write_cxc_file")
def test_run_csv2cxc_with_config_label_residues_forwarded_as_override(mock_write_cxc_file):
    cfg = {"model_id": 1, "sources": [{"name": "main", "input": "csv_dir", "label_residues": False}]}

    run_csv2cxc_with_config("out.cxc", config=cfg, label_residues=True)

    _, kwargs = mock_write_cxc_file.call_args
    assert kwargs["label_residues_override"] is True


@patch("pliparser.core.write_cxc_file")
def test_run_csv2cxc_with_config_label_residues_none_by_default(mock_write_cxc_file):
    cfg = {"model_id": 1, "sources": [{"name": "main", "input": "csv_dir", "label_residues": True}]}

    run_csv2cxc_with_config("out.cxc", config=cfg)

    _, kwargs = mock_write_cxc_file.call_args
    assert kwargs["label_residues_override"] is None


@patch("pliparser.core.write_cxc_file")
def test_run_csv2cxc_with_config_path_resolves_relative_source_inputs(mock_write_cxc_file, tmp_path: Path) -> None:
    (tmp_path / "csvs").mkdir()
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(
        json.dumps({"model_id": 1, "chains": _MIN_CHAINS, "sources": [{"name": "main", "input": "csvs"}]}),
        encoding="UTF-8",
    )

    run_csv2cxc_with_config("out.cxc", config_path=cfg_file)

    resolved_config = mock_write_cxc_file.call_args[0][1]
    assert resolved_config["sources"][0]["input"] == str((tmp_path / "csvs").resolve())


@patch("pliparser.core.write_cxc_file")
def test_run_csv2cxc_with_config_path_leaves_absolute_source_inputs_untouched(mock_write_cxc_file, tmp_path: Path) -> None:
    absolute_input = str(tmp_path / "csvs")
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(
        json.dumps({"model_id": 1, "chains": _MIN_CHAINS, "sources": [{"name": "main", "input": absolute_input}]}),
        encoding="UTF-8",
    )

    run_csv2cxc_with_config("out.cxc", config_path=cfg_file)

    resolved_config = mock_write_cxc_file.call_args[0][1]
    assert resolved_config["sources"][0]["input"] == absolute_input


@patch("pliparser.core.plip2csv_stream")
def test_run_plip2csv_converts_to_path_objects(mock_plip2csv_stream):
    run_plip2csv("input.txt", "output_dir")

    mock_plip2csv_stream.assert_called_once()
    call_args = mock_plip2csv_stream.call_args[0]
    assert isinstance(call_args[0], Path)
    assert isinstance(call_args[1], Path)
    assert call_args[0] == Path("input.txt")
    assert call_args[1] == Path("output_dir")
