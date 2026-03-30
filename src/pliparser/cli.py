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
    return parser.parse_args(args=args)


def run(args=None):
    args = get_arguments(args=args)

    if args.subcommand == "plip2csv":
        run_plip2csv(args.input, args.output)
        return

    raise ValueError(f"Unknown subcommand: {args.subcommand}")
