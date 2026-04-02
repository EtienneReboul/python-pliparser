import json
from pathlib import Path
from typing import Union

from pliparser.csv2cxc import write_cxc_file
from pliparser.plip2csv import plip2csv_stream


def read_json_config(path: Path) -> dict:
    """
    Read a JSON configuration file and return its contents as a dictionary.

    Parameters
    ----------
    path : Path
        The file path to the JSON configuration file.

    Returns
    -------
    dict
        A dictionary containing the parsed contents of the JSON file.

    Raises
    ------
    FileNotFoundError
        If the specified JSON file does not exist.
    json.JSONDecodeError
        If there is an error parsing the JSON file.
    """
    with path.open("r", encoding="UTF-8") as file:
        config = json.load(file)
    return config


def run_plip2csv(input_path: Union[str, Path], output_dir: Union[str, Path]) -> None:
    """Convert a PLIP report to CSV files using the streaming implementation."""

    plip2csv_stream(Path(input_path), Path(output_dir))


def run_csv2cxc_with_config(
    input_csv_path: Union[str, Path],
    output_cxc_path: Union[str, Path],
    config: dict | None = None,
    config_path: Union[str, Path, None] = None,
) -> None:
    """Convert interaction CSV files to a CXC file using JSON or CLI config.

    Parameters
    ----------
    input_csv_path : Union[str, Path]
        Directory containing interaction CSV files.
    output_cxc_path : Union[str, Path]
        Destination CXC file path.
    config : dict | None
        Parsed config values, typically from CLI flags.
    config_path : Union[str, Path, None]
        Optional JSON config path. When provided, JSON takes precedence and
        ``config`` is ignored.
    """
    if config_path is not None:
        resolved_config = read_json_config(Path(config_path))
    elif config is not None:
        resolved_config = config
    else:
        raise ValueError("Either 'config_path' or 'config' must be provided for csv2cxc")

    write_cxc_file(Path(input_csv_path), Path(output_cxc_path), resolved_config)


def run_csv2cxc(input_csv_path: Union[str, Path], output_cxc_path: Union[str, Path], config_path: Union[str, Path]) -> None:
    """Backward-compatible wrapper for JSON-config csv2cxc execution."""

    run_csv2cxc_with_config(input_csv_path, output_cxc_path, config_path=config_path)
