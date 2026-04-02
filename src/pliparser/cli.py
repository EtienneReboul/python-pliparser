"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mpliparser` python will execute
    ``__main__.py`` as a script. That means there will not be any
    ``pliparser.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there"s no ``pliparser.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

import argparse

from .core import run_csv2cxc_with_config
from .core import run_plip2csv


def get_arguments(args=None):
    """Parse command line arguments and return them as a namespace."""
    parser = argparse.ArgumentParser(description="Command description.")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    plip2csv_parser = subparsers.add_parser("plip2csv", help="Convert a PLIP report to CSV files.")
    plip2csv_parser.add_argument(
        "--input",
        required=True,
        help="Path to the input PLIP TXT report.",
    )
    plip2csv_parser.add_argument(
        "--output",
        required=True,
        help="Directory where CSV files will be written.",
    )

    csv2cxc_parser = subparsers.add_parser("csv2cxc", help="Convert PLIP CSV interactions to ChimeraX CXC.")
    csv2cxc_parser.add_argument("--input", required=True, help="Directory containing interaction CSV files.")
    csv2cxc_parser.add_argument("--output", required=True, help="Path to output CXC file.")
    csv2cxc_parser.add_argument("--config", help="Path to JSON config file.")

    # These options are required only when --config is not provided.
    csv2cxc_parser.add_argument("--pdb", help="PDB path or identifier to open in ChimeraX.")
    csv2cxc_parser.add_argument("--model-id", type=int, help="ChimeraX model id.")
    csv2cxc_parser.add_argument("--receptor-chain", help="Receptor chain id.")
    csv2cxc_parser.add_argument("--ligand-chain", help="Ligand chain id.")
    csv2cxc_parser.add_argument("--transparency", type=int, help="Receptor transparency value.")
    csv2cxc_parser.add_argument("--receptor-color", help="Receptor color.")
    csv2cxc_parser.add_argument("--ligand-color", help="Ligand color.")
    csv2cxc_parser.add_argument(
        "--issmalmol",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Whether ligand is treated as a small molecule.",
    )

    parsed_args = parser.parse_args(args=args)

    if parsed_args.subcommand == "csv2cxc" and parsed_args.config is None:
        required_if_no_json = [
            "pdb",
            "model_id",
            "receptor_chain",
            "ligand_chain",
            "transparency",
            "receptor_color",
            "ligand_color",
            "issmalmol",
        ]
        missing = [name for name in required_if_no_json if getattr(parsed_args, name) is None]
        if missing:
            parser.error(
                "csv2cxc requires --config or all explicit options: " + ", ".join(f"--{name.replace('_', '-')}" for name in missing)
            )

    return parsed_args


def run(args=None):
    args = get_arguments(args=args)

    if args.subcommand == "plip2csv":
        run_plip2csv(args.input, args.output)
        return

    if args.subcommand == "csv2cxc":
        config = None
        if args.config is None:
            config = {
                "pdb": args.pdb,
                "model_id": args.model_id,
                "receptor_chain": args.receptor_chain,
                "ligand_chain": args.ligand_chain,
                "transparency": args.transparency,
                "issmalmol": args.issmalmol,
                "receptor_color": args.receptor_color,
                "ligand_color": args.ligand_color,
            }

        run_csv2cxc_with_config(args.input, args.output, config=config, config_path=args.config)
        return

    raise ValueError(f"Unknown subcommand: {args.subcommand}")
