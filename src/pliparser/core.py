import json
from pathlib import Path
from typing import Optional
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
    output_cxc_path: Union[str, Path],
    config: Optional[dict] = None,
    config_path: Optional[Union[str, Path]] = None,
    interaction_types: Optional[set[str]] = None,
    label_residues: Optional[bool] = None,
) -> None:
    """Convert interaction CSV files to a CXC file using JSON or CLI config.

    Parameters
    ----------
    output_cxc_path : Union[str, Path]
        Destination CXC file path.
    config : Optional[dict]
        Parsed config values, typically from CLI flags. Must contain a 'sources' list
        whose entries carry their own 'input' CSV directory (see ``write_cxc_file``).
    config_path : Optional[Union[str, Path]]
        Optional JSON config path. When provided, JSON takes precedence and
        ``config`` is ignored. Each source's 'input' path is resolved relative to
        this file's directory when it is not already absolute.
    interaction_types : Optional[set[str]]
        Global interaction-type filter forwarded to ``write_cxc_file``, overriding
        every source's own filter.
    label_residues : Optional[bool]
        When set, overrides every source's ``label_residues`` value. This lets the
        CLI's ``--label-residues``/``--no-label-residues`` flags take effect even
        when ``--config`` (JSON) is used. Leave as None to use each source's own value.
    """
    if config_path is not None:
        resolved_config = read_json_config(Path(config_path))
        base_dir = Path(config_path).resolve().parent
        for source in resolved_config.get("sources", []):
            source_input = Path(source["input"])
            if not source_input.is_absolute():
                source["input"] = str((base_dir / source_input).resolve())
    elif config is not None:
        resolved_config = config
    else:
        raise ValueError("Either 'config_path' or 'config' must be provided for csv2cxc")

    write_cxc_file(
        Path(output_cxc_path),
        resolved_config,
        interaction_types=interaction_types,
        label_residues_override=label_residues,
    )
