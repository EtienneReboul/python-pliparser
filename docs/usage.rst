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

Create a config file (for example ``cxc-config.json``). The ``chains`` list gives every
chain (or comma-joined chain group) its own color, transparency, and show/hide status,
and the ``sources`` list points at one or more directories of interaction CSVs (a single
directory here; see "Multi-Source Aggregation" below for more than one):

.. code-block:: json

        {
            "pdb": "1vsn",
            "model_id": 1,
            "chains": [
                {"chain": "A", "color": "gray", "transparency": 65},
                {"chain": "A", "color": "green", "small_molecule": true}
            ],
            "sources": [
                {"name": "main", "input": "out/csv/", "issmalmol": true}
            ]
        }

Then generate the ChimeraX command script:

.. code-block:: bash

        pliparser csv2cxc \
            --output out/cxc/complex.cxc \
            --config cxc-config.json

Example 3: CSV to ChimeraX CXC (without JSON)
==============================================

For a single PLIP CSV source, you can also pass all required visualization options
directly on the command line, using ``--primary-*`` for one chain group and
``--partner-*`` for the other (a single PLIP run only ever has two sides, so the flat
CLI only supports these two groups; use ``--config`` for more chains or more sources):

.. code-block:: bash

        pliparser csv2cxc \
            --input out/csv/ \
            --output out/cxc/complex.cxc \
            --pdb 1vsn \
            --model-id 1 \
            --primary-chain A \
            --primary-color gray \
            --primary-transparency 65 \
            --partner-chain A \
            --partner-color green \
            --partner-small-molecule

Example 4: Filtering interaction types
======================================

Use ``--interaction-types`` to restrict the output to a subset of interaction types.
This is particularly useful for intra- or inter-chain analyses where hydrophobic
interactions and hydrogen bonds would clutter the visualisation.

Pass the types you want to **include** as a space-separated list. Matching is
substring-based, so ``halogen_bond`` matches both ``halogen_bond`` and
``halogen_bonds``. In JSON config mode, each source in ``sources`` can also set its own
``"interaction_types"`` list; the ``--interaction-types`` CLI flag, when given, overrides
every source's own list.

.. code-block:: bash

        pliparser csv2cxc \
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
            --primary-chain A \
            --primary-color gray \
            --primary-transparency 65 \
            --partner-chain A \
            --partner-color green \
            --partner-small-molecule \
            --interaction-types pi-stacking salt_bridge

Example 5: Labeling interacting residues
=========================================

Use ``--label-residues`` to add ChimeraX text labels (residue type, number, and
chain) on every residue pair involved in an interaction. In JSON config mode, each
source can also set its own ``"label_residues"``; the ``--label-residues`` CLI flag,
when given, overrides every source's own value.

.. code-block:: bash

        pliparser csv2cxc \
            --output out/cxc/complex-labeled.cxc \
            --config cxc-config.json \
            --label-residues

The flag can also be set per source in the JSON config via ``"label_residues": true``.

Notes
=====

- ``--config`` is optional for ``csv2cxc``.
- ``--input`` and ``--config`` are mutually exclusive: in JSON-config mode, every
  source's CSV directory comes from that source's ``"input"`` field in the config
  instead (resolved relative to the config file's own directory when relative).
- If ``--config`` is not provided, ``--input`` plus all explicit ``--primary-*``/
  ``--partner-*`` visualization options are required (``--partner-color`` unless
  ``--partner-small-molecule`` is set).
- ``--interaction-types`` is optional. When omitted, each source's own filter (or all
  interaction types, if unset) is used.
- ``--label-residues`` is optional and, when omitted, each source's own value is used
  (default off).
- Generated ``.cxc`` files can be opened directly in ChimeraX.

CI End-to-End Example (as in GitHub Actions)
=============================================

The ``integration-plip-testsuite`` job in ``.github/workflows/github-actions.yml`` runs
this exact pipeline against a curated set of PDB structures taken from `PLIP's own test
suite <https://github.com/pharmai/plip/tree/master/plip/test/pdb>`_, chosen so that every
PLIP interaction type (hydrophobic, hydrogen bond, water bridge, salt bridge, pi-stacking,
pi-cation, halogen bond, metal complex) plus DNA/RNA primary chain, DNA partner, peptide
partner, and NMR-ensemble scenarios are each exercised at least once. A separate
``integration-multi-source-9kbz`` job (see "Multi-Source Aggregation" below) covers the
multi-source aggregation feature:

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
      "chains": [
        {"chain": "A", "color": "gray", "transparency": 65},
        {"chain": "A", "color": "green", "small_molecule": true}
      ],
      "sources": [
        {"name": "main", "input": "integration-data/csv/1acj", "issmalmol": true}
      ]
    }
    JSON

    pliparser csv2cxc \
      --output integration-data/cxc/1acj.cxc \
      --config integration-data/cxc/csv2cxc-config-1acj.json

Step 4: Quick output checks
---------------------------

.. code-block:: bash

    test -f integration-data/csv/1acj/pi-stacking.csv
    test -s integration-data/cxc/1acj.cxc
    grep -q "name pi-stacking" integration-data/cxc/1acj.cxc

Macromolecule primary/partner example (nucleic acid primary chain)
--------------------------------------------------------------------

For a nucleic-acid primary chain with a macromolecule (protein) partner, PLIP needs the
``--dnareceptor`` flag (it applies to RNA as well as DNA) plus an explicit ``--chains``
grouping, and ``csv2cxc`` needs ``--partner-small-molecule`` left unset so the whole
partner chain is shown instead of just its heteroatoms. This reproduces the ``9kbz``
matrix entry (see "Multi-Source Aggregation" below for a richer example using the same
structure):

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
      --primary-chain C,D \
      --primary-color gray \
      --primary-transparency 65 \
      --partner-chain A,B \
      --partner-color cornflowerblue

Multi-Source Aggregation (JSON config only)
=============================================

Sometimes one structure has more than two biologically distinct chains, and you want to
run PLIP more than once with different chain groupings, then view every chain's
interactions together with each chain colored independently. This needs a JSON config,
since it requires a ``chains`` list with more than two entries and a ``sources`` list
with more than one entry.

PDB `9KBZ <https://www.rcsb.org/structure/9KBZ>`_ (a cryo-EM structure of the plant
Dicer-like 4 / Double-stranded RNA-binding protein 4 / dsRNA complex) is a good example:
chain **A** is DCL4 (protein), chain **B** is DRB4 (protein), and chains **C**/**D** are
the RNA duplex. A single PLIP run can only ever report one receptor side and one ligand
side, so seeing *both* DCL4-RNA interactions and DCL4-DRB4 interactions in the same view
means running PLIP twice with different ``--chains`` groupings, then aggregating both
CSV sets into one ``.cxc``.

Step 1: Generate two PLIP reports with different chain groupings
--------------------------------------------------------------------

.. code-block:: bash

    # DCL4 (A) vs RNA (C,D)
    mkdir -p integration-data/raw/9kbz-dcl4-rna
    docker run --rm \
      -v "${PWD}/integration-data/raw/9kbz-dcl4-rna:/results" \
      -w /results \
      --user "$(id -u):$(id -g)" \
      pharmai/plip:latest -i 9kbz -t --dnareceptor --chains "[['C','D'], ['A']]"

    # DCL4 (A) vs DRB4 (B)
    mkdir -p integration-data/raw/9kbz-dcl4-drb4
    docker run --rm \
      -v "${PWD}/integration-data/raw/9kbz-dcl4-drb4:/results" \
      -w /results \
      --user "$(id -u):$(id -g)" \
      pharmai/plip:latest -i 9kbz -t --chains "[['A'], ['B']]"

Step 2: Convert both reports to CSV
--------------------------------------

.. code-block:: bash

    for RUN in 9kbz-dcl4-rna 9kbz-dcl4-drb4; do
      mkdir -p "integration-data/csv/${RUN}"
      REPORT_PATH="$(find "integration-data/raw/${RUN}" -type f -name '*.txt' | head -n 1)"
      pliparser plip2csv --input "$REPORT_PATH" --output "integration-data/csv/${RUN}"
    done

Step 3: Aggregate both sources into one CXC
------------------------------------------------

Each chain gets its own entry in ``chains`` (three chains here, not two), and each PLIP
run gets its own entry in ``sources``, with independent ``issmalmol``/``label_residues``/
``interaction_types`` settings. Marker-set model ids are allocated across both sources so
they never collide, and each source's ``rename`` commands are prefixed with its ``name``
(``dcl4_rna_...`` / ``dcl4_drb4_...``) so identical interaction-type filenames from the
two runs (e.g. both producing ``hydrogen_bonds.csv``) stay distinguishable in ChimeraX.

.. code-block:: bash

    mkdir -p integration-data/cxc
    cat > integration-data/cxc/csv2cxc-config-9kbz-multisource.json <<'JSON'
    {
      "pdb": "9kbz",
      "model_id": 1,
      "chains": [
        {"chain": "A",   "color": "gray",          "transparency": 0},
        {"chain": "B",   "color": "orange",         "transparency": 0},
        {"chain": "C,D", "color": "cornflowerblue", "transparency": 65}
      ],
      "sources": [
        {"name": "dcl4_rna",  "input": "integration-data/csv/9kbz-dcl4-rna",  "issmalmol": false},
        {"name": "dcl4_drb4", "input": "integration-data/csv/9kbz-dcl4-drb4", "issmalmol": false, "label_residues": true}
      ]
    }
    JSON

    pliparser csv2cxc \
      --output integration-data/cxc/9kbz-multisource.cxc \
      --config integration-data/cxc/csv2cxc-config-9kbz-multisource.json

The resulting ``.cxc`` opens 9KBZ once, colors chain A gray, chain B orange, and chains
C/D cornflowerblue (at 65% transparency), and overlays both sets of interactions on the
same structure -- DCL4-RNA markers from the ``dcl4_rna`` source and DCL4-DRB4 markers
(with residue labels) from the ``dcl4_drb4`` source.
