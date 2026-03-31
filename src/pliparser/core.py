from pathlib import Path
from typing import Union

from pliparser.plip2csv import plip2csv_stream


def run_plip2csv(input_path: Union[str, Path], output_dir: Union[str, Path]) -> None:
    """Convert a PLIP report to CSV files using the streaming implementation."""

    plip2csv_stream(Path(input_path), Path(output_dir))
