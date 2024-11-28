#!/usr/bin/env python
"""
setup.py

setup is used to create an editable package for the python code in the
src directory. It can be imported just like any other package, so we
avoid any steps to update the PYTHONPATH at the start of a notebook.
"""

from setuptools import setup

setup(
    name="ebird-notebooks",
    version="0.0.0",
    description="Jupyter notebooks for analysing eBird checklists",
    packages=["main"],
    package_dir={"": "src"},
)
