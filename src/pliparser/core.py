from pathlib import Path

from pliparser.plip2csv import plip2csv_stream


def compute(names: list[str]) -> str:
    """Return the longest string from the input list."""

    return max(names, key=len)


def run_plip2csv(input_path: str | Path, output_dir: str | Path) -> None:
    """Convert a PLIP report to CSV files using the streaming implementation."""

    plip2csv_stream(Path(input_path), Path(output_dir))
