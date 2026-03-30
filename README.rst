========
Overview
========


.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - |github-actions| |codecov|
    * - package
      - |version| |wheel| |supported-versions| |supported-implementations| |commits-since|
.. |docs| image:: https://readthedocs.org/projects/python-pliparser/badge/?style=flat
    :target: https://readthedocs.org/projects/python-pliparser/
    :alt: Documentation Status
.. |github-actions| image:: https://github.com/EtienneReboul/python-pliparser/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/EtienneReboul/python-pliparser/actions
.. |codecov| image:: https://codecov.io/gh/EtienneReboul/python-pliparser/branch/main/graphs/badge.svg?branch=main
    :alt: Coverage Status
    :target: https://app.codecov.io/github/EtienneReboul/python-pliparser
.. |version| image:: https://img.shields.io/pypi/v/pliparser.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/pliparser
.. |wheel| image:: https://img.shields.io/pypi/wheel/pliparser.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/pliparser
.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/pliparser.svg
    :alt: Supported versions
    :target: https://pypi.org/project/pliparser
.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/pliparser.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/pliparser
.. |commits-since| image:: https://img.shields.io/github/commits-since/EtienneReboul/python-pliparser/v0.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/EtienneReboul/python-pliparser/compare/v0.0.0...main


Small standalone package with only built-in dependencies for parsing plip report to csv and create command scprit for
ChimeraX

* Free software: BSD 2-Clause License

Installation
============

::

    pip install pliparser

You can also install the in-development version with::

    pip install https://github.com/EtienneReboul/python-pliparser/archive/main.zip


Documentation
=============


https://python-pliparser.readthedocs.io/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
