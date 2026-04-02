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


def run_csv2cxc(input_csv_path: Union[str, Path], output_cxc_path: Union[str, Path], config_path: Union[str, Path]) -> None:
    """Convert a CSV file to a CXC file using the streaming implementation."""

    config = read_json_config(Path(config_path))
    write_cxc_file(Path(input_csv_path), Path(output_cxc_path), config)
