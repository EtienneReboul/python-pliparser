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
.. |docs| image:: https://readthedocs.org/projects/python-pliparser/badge/?version=latest
    :target: https://python-pliparser.readthedocs.io/en/latest/index.html
    :alt: Read the Docs Status
.. |github-actions| image:: https://github.com/EtienneReboul/python-pliparser/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/EtienneReboul/python-pliparser/actions
.. |codecov| image:: https://codecov.io/gh/EtienneReboul/python-pliparser/branch/main/graphs/badge.svg?branch=main
    :alt: Coverage Status
    :target: https://app.codecov.io/github/EtienneReboul/python-pliparser
.. |version| image:: https://img.shields.io/pypi/v/python-pliparser.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/python-pliparser
.. |wheel| image:: https://img.shields.io/pypi/wheel/python-pliparser.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/python-pliparser
.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/python-pliparser.svg
    :alt: Supported versions
    :target: https://pypi.org/project/python-pliparser
.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/python-pliparser.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/python-pliparser
.. |commits-since| image:: https://img.shields.io/github/commits-since/EtienneReboul/python-pliparser/0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/EtienneReboul/python-pliparser/commits/main


Small standalone package with only built-in dependencies for parsing plip report to csv and create command scprit for
ChimeraX

* Free software: BSD 2-Clause License

Installation
============

::

    pip install python-pliparser

You can also install the in-development version with::

    pip install https://github.com/EtienneReboul/python-pliparser/archive/main.zip


Documentation
=============


https://python-pliparser.readthedocs.io/en/latest/index.html


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
