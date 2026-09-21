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
    csv2cxc_parser.add_argument(
        "--input",
        help="Directory containing interaction CSV files for a single source. "
        "Cannot be combined with --config; in JSON-config mode every source's input "
        "directory comes from the config's 'sources' list instead.",
    )
    csv2cxc_parser.add_argument("--output", required=True, help="Path to output CXC file.")
    csv2cxc_parser.add_argument("--config", help="Path to JSON config file.")

    # These options are single-source-only: they are required when --config is not
    # provided, and rejected when it is.
    csv2cxc_parser.add_argument("--pdb", help="PDB path or identifier to open in ChimeraX.")
    csv2cxc_parser.add_argument("--model-id", type=int, help="ChimeraX model id.")
    csv2cxc_parser.add_argument("--primary-chain", help="Primary chain id (e.g. the structure's main receiving chain).")
    csv2cxc_parser.add_argument("--primary-color", help="Primary chain color.")
    csv2cxc_parser.add_argument("--primary-transparency", type=int, default=None, help="Primary chain transparency value.")
    csv2cxc_parser.add_argument("--partner-chain", help="Partner chain id (the other side of the interaction).")
    csv2cxc_parser.add_argument("--partner-color", help="Partner chain color. Required unless --partner-small-molecule is set.")
    csv2cxc_parser.add_argument("--partner-transparency", type=int, default=None, help="Partner chain transparency value.")
    csv2cxc_parser.add_argument(
        "--partner-small-molecule",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Whether the partner chain is treated as a small molecule.",
    )
    csv2cxc_parser.add_argument(
        "--interaction-types",
        nargs="+",
        default=None,
        metavar="TYPE",
        help="Subset of interaction types to include (e.g. pi-stacking salt_bridge). Omit to include all.",
    )
    csv2cxc_parser.add_argument(
        "--label-residues",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Add ChimeraX labels to residues involved in interactions. "
        "Applies with --config too; omit to fall back to the config value (default: no labels).",
    )

    parsed_args = parser.parse_args(args=args)

    if parsed_args.subcommand == "csv2cxc":
        flat_only_flags = [
            "pdb",
            "model_id",
            "primary_chain",
            "primary_color",
            "primary_transparency",
            "partner_chain",
            "partner_color",
            "partner_transparency",
            "partner_small_molecule",
        ]
        if parsed_args.config is not None:
            if parsed_args.input is not None:
                parser.error(
                    "csv2cxc: --input cannot be combined with --config; put each source's "
                    "'input' path inside the JSON config's 'sources' list instead."
                )
            set_flat_flags = [name for name in flat_only_flags if getattr(parsed_args, name) is not None]
            if set_flat_flags:
                parser.error(
                    "csv2cxc: these flags are single-source-only and cannot be combined with --config: "
                    + ", ".join(f"--{name.replace('_', '-')}" for name in set_flat_flags)
                )
        else:
            required_if_no_json = ["input", "pdb", "model_id", "primary_chain", "primary_color", "partner_chain"]
            missing = [name for name in required_if_no_json if getattr(parsed_args, name) is None]
            if not parsed_args.partner_small_molecule and parsed_args.partner_color is None:
                missing.append("partner_color")
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
                "chains": [
                    {
                        "chain": args.primary_chain,
                        "color": args.primary_color,
                        "transparency": args.primary_transparency or 0,
                        "show": True,
                    },
                    {
                        "chain": args.partner_chain,
                        "color": args.partner_color,
                        "transparency": args.partner_transparency or 0,
                        "show": True,
                        "small_molecule": bool(args.partner_small_molecule),
                    },
                ],
                "sources": [
                    {
                        "name": "source",
                        "input": args.input,
                        "issmalmol": bool(args.partner_small_molecule),
                        "label_residues": bool(args.label_residues),
                    }
                ],
            }

        interaction_types = set(args.interaction_types) if args.interaction_types else None
        run_csv2cxc_with_config(
            args.output,
            config=config,
            config_path=args.config,
            interaction_types=interaction_types,
            label_residues=args.label_residues,
        )
        return

    raise ValueError(f"Unknown subcommand: {args.subcommand}")
