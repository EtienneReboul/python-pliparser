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
