
Changelog
=========

0.1.4 (2026-06-03)
------------------

* Added ``--interaction-types`` flag to ``csv2cxc`` to restrict output to a subset of interaction types (e.g. exclude hydrophobic interactions and hydrogen bonds). The flag is available on both the CLI and the Python API (``write_cxc_file``, ``run_csv2cxc_with_config``).
* Fixed ``write2csv`` to write the ``interaction_type`` column in per-interaction CSV files and the summary, making it consistent with ``plip2csv_stream``.
* Removed ``taplo-lint`` pre-commit hook whose remote schema-catalog fetch was broken in v0.9.3, unblocking the ``check`` CI job.
* Added ``.pre-commit-config.yaml`` and ``.taplo.toml`` to the CI path triggers so linting-config changes are validated automatically.
* Extended integration tests with a filtered-CXC use case that verifies hydrophobic and hydrogen bond interactions are absent from the output.
* Updated usage documentation with an ``--interaction-types`` example.

0.1.3 (2026-04-15)
------------------

* Fix pi-cation interaction handling in the CSV-to-CXC conversion workflow, ensuring correct annotation and pseudobond styling.
* Simplify pseudobond management logic by updating pbond dataclasses.

0.1.2 (2026-04-08)
------------------

* Expanded metal-binding handling and interaction rendering in the CSV-to-CXC conversion workflow.
* Improved pi-stacking processing and pseudobond styling selection using PLIP stacking type hints.
* Added backward-compatible typing annotations for Python 3.9 compatibility in pi-stacking pseudobond parameter selection.
* Updated unit tests to cover pi-stacking annotation behavior and related mapping paths.

0.1.1 (2026-04-07)
------------------

* Updated documentation content with detailed end-to-end usage examples (PLIP report -> CSV -> CXC).
* Added CI-aligned documentation steps, including the Docker command used to generate PLIP reports.
* Updated README links and badges to reflect Read the Docs hosting and current PyPI project metadata.

0.1.0 (2026-04-07)
------------------

* Published release 0.1.0.
* Added ``csv2cxc`` CLI workflow and end-to-end conversion from PLIP report to CSV to CXC.
* Updated packaging/distribution metadata for PyPI publication as ``python-pliparser``.

0.0.0 (2026-03-30)
------------------

* First release on PyPI.
