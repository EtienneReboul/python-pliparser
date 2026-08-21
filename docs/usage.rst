=====
Usage
=====

The CLI provides two main steps:

1. Convert a PLIP text report to structured CSV files.
2. Convert those CSV files to a ChimeraX ``.cxc`` command script.

PLIP report -> CSV -> CXC

Example 1: PLIP report to CSV
=============================

Convert a PLIP text report into one CSV per interaction type plus a summary file.

.. code-block:: bash

        pliparser plip2csv \
            --input report.txt \
            --output out/csv/

Expected output in ``out/csv/`` includes files such as:

- ``hydrogen_bonds.csv``
- ``hydrophobic_interactions.csv``
- ``halogen_bonds.csv``
- ``summary.csv``

Example 2: CSV to ChimeraX CXC (with JSON config)
==================================================

Create a config file (for example ``cxc-config.json``):

.. code-block:: json

        {
            "pdb": "1vsn",
            "model_id": 1,
            "receptor_chain": "A",
            "ligand_chain": "A",
            "transparency": 65,
            "issmalmol": true,
            "receptor_color": "gray",
            "ligand_color": "green"
        }

Then generate the ChimeraX command script:

.. code-block:: bash

        pliparser csv2cxc \
            --input out/csv/ \
            --output out/cxc/complex.cxc \
            --config cxc-config.json

Example 3: CSV to ChimeraX CXC (without JSON)
==============================================

You can also pass all required visualization options directly on the command line:

.. code-block:: bash

        pliparser csv2cxc \
            --input out/csv/ \
            --output out/cxc/complex.cxc \
            --pdb 1vsn \
            --model-id 1 \
            --receptor-chain A \
            --ligand-chain A \
            --transparency 65 \
            --issmalmol \
            --receptor-color gray \
            --ligand-color green

Example 4: Filtering interaction types
======================================

Use ``--interaction-types`` to restrict the output to a subset of interaction types.
This is particularly useful for intra- or inter-chain analyses where hydrophobic
interactions and hydrogen bonds would clutter the visualisation.

Pass the types you want to **include** as a space-separated list. Matching is
substring-based, so ``halogen_bond`` matches both ``halogen_bond`` and
``halogen_bonds``.

.. code-block:: bash

        pliparser csv2cxc \
            --input out/csv/ \
            --output out/cxc/complex-filtered.cxc \
            --config cxc-config.json \
            --interaction-types pi-stacking pi-cation water_bridge salt_bridge halogen_bond metal_complexes

The flag is compatible with both ``--config`` and the explicit option form:

.. code-block:: bash

        pliparser csv2cxc \
            --input out/csv/ \
            --output out/cxc/complex-filtered.cxc \
            --pdb 1vsn \
            --model-id 1 \
            --receptor-chain A \
            --ligand-chain A \
            --transparency 65 \
            --issmalmol \
            --receptor-color gray \
            --ligand-color green \
            --interaction-types pi-stacking salt_bridge

Example 5: Labeling interacting residues
=========================================

Use ``--label-residues`` to add ChimeraX text labels (residue type, number, and
chain) on every receptor and ligand residue involved in an interaction.

.. code-block:: bash

        pliparser csv2cxc \
            --input out/csv/ \
            --output out/cxc/complex-labeled.cxc \
            --config cxc-config.json \
            --label-residues

The flag can also be set to ``true`` in the JSON config via ``"label_residues": true``.

Notes
=====

- ``--config`` is optional for ``csv2cxc``.
- If ``--config`` is not provided, all explicit visualization options are required.
- ``--interaction-types`` is optional. When omitted, all interaction types are included.
- ``--label-residues`` is optional and defaults to off.
- Generated ``.cxc`` files can be opened directly in ChimeraX.

CI End-to-End Example (as in GitHub Actions)
=============================================

The ``integration-plip-testsuite`` job in ``.github/workflows/github-actions.yml`` runs
this exact pipeline against a curated set of PDB structures taken from `PLIP's own test
suite <https://github.com/pharmai/plip/tree/master/plip/test/pdb>`_, chosen so that every
PLIP interaction type (hydrophobic, hydrogen bond, water bridge, salt bridge, pi-stacking,
pi-cation, halogen bond, metal complex) plus DNA/RNA-receptor, DNA-ligand, peptide-ligand,
and NMR-ensemble scenarios are each exercised at least once:

1. Generate a real PLIP report with Docker.
2. Convert the report to CSV.
3. Convert CSV to CXC (JSON config, explicit CLI flags, ``--label-residues``, and
   ``--interaction-types`` filtering are all exercised for every structure).
4. Validate that output files exist, are non-empty, and contain the expected interaction
   type.

The commands below reproduce the ``1acj`` matrix entry (Tacrine bound to
acetylcholinesterase, a pi-stacking interaction) end to end.

Step 1: Generate the PLIP report with Docker
---------------------------------------------

.. code-block:: bash

    mkdir -p integration-data/raw/1acj
    docker run --rm \
      -v "${PWD}/integration-data/raw/1acj:/results" \
      -w /results \
      --user "$(id -u):$(id -g)" \
      pharmai/plip:latest -i 1acj -t

Step 2: Convert PLIP report to CSV
----------------------------------

.. code-block:: bash

    mkdir -p integration-data/csv/1acj
    REPORT_PATH="$(find integration-data/raw/1acj -type f -name '*.txt' | head -n 1)"
    pliparser plip2csv --input "$REPORT_PATH" --output integration-data/csv/1acj

Step 3: Convert CSV to CXC
--------------------------

.. code-block:: bash

    mkdir -p integration-data/cxc
    cat > integration-data/cxc/csv2cxc-config-1acj.json <<'JSON'
    {
      "pdb": "1acj",
      "model_id": 1,
      "receptor_chain": "A",
      "ligand_chain": "A",
      "transparency": 65,
      "issmalmol": true,
      "receptor_color": "gray",
      "ligand_color": "green"
    }
    JSON

    pliparser csv2cxc \
      --input integration-data/csv/1acj \
      --output integration-data/cxc/1acj.cxc \
      --config integration-data/cxc/csv2cxc-config-1acj.json

Step 4: Quick output checks
---------------------------

.. code-block:: bash

    test -f integration-data/csv/1acj/pi-stacking.csv
    test -s integration-data/cxc/1acj.cxc
    grep -q "name pi-stacking" integration-data/cxc/1acj.cxc

Macromolecule receptor/ligand example (nucleic acid receptor)
---------------------------------------------------------------

For a nucleic-acid receptor with a macromolecule (protein) ligand, PLIP needs the
``--dnareceptor`` flag (it applies to RNA as well as DNA) plus an explicit ``--chains``
grouping, and ``csv2cxc`` needs ``issmalmol: false`` so the whole ligand chain is shown
instead of just its heteroatoms. This reproduces the ``9kbz`` matrix entry:

.. code-block:: bash

    docker run --rm \
      -v "${PWD}/integration-data/raw/9kbz:/results" \
      -w /results \
      --user "$(id -u):$(id -g)" \
      pharmai/plip:latest -i 9kbz -t --dnareceptor --chains "[['C','D'], ['A','B']]"

    pliparser csv2cxc \
      --input integration-data/csv/9kbz \
      --output integration-data/cxc/9kbz.cxc \
      --pdb 9kbz \
      --model-id 1 \
      --receptor-chain C,D \
      --ligand-chain A,B \
      --transparency 65 \
      --no-issmalmol \
      --receptor-color gray \
      --ligand-color cornflowerblue
