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

Notes
=====

- ``--config`` is optional for ``csv2cxc``.
- If ``--config`` is not provided, all explicit visualization options are required.
- Generated ``.cxc`` files can be opened directly in ChimeraX.

CI End-to-End Example (as in GitHub Actions)
=============================================

The integration job in ``.github/workflows/github-actions.yml`` validates the full pipeline:

1. Generate a real PLIP report with Docker.
2. Convert the report to CSV.
3. Convert CSV to CXC.
4. Validate that output files exist and are non-empty.

Step 1: Generate the PLIP report with Docker
---------------------------------------------

.. code-block:: bash

    mkdir -p integration-data/raw/1vsn
    docker run --rm \
      -v "${PWD}/integration-data/raw/1vsn:/results" \
      -w /results \
      --user "$(id -u):$(id -g)" \
      pharmai/plip:latest -i 1vsn -t

Step 2: Convert PLIP report to CSV
----------------------------------

.. code-block:: bash

    mkdir -p integration-data/csv
    REPORT_PATH="$(find integration-data/raw/1vsn -type f -name '*.txt' | head -n 1)"
    pliparser plip2csv --input "$REPORT_PATH" --output integration-data/csv

Step 3: Convert CSV to CXC
--------------------------

.. code-block:: bash

    mkdir -p integration-data/cxc
    cat > integration-data/cxc/csv2cxc-config.json <<'JSON'
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
    JSON

    pliparser csv2cxc \
      --input integration-data/csv \
      --output integration-data/cxc/1vsn.cxc \
      --config integration-data/cxc/csv2cxc-config.json

Step 4: Quick output checks
---------------------------

.. code-block:: bash

    find integration-data/csv -type f -name '*.csv'
    test -s integration-data/cxc/1vsn.cxc
