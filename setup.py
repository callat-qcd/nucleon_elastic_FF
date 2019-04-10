# -*- coding: utf-8 -*-
"""Setup file for nucleon_elastic_FF
"""
__author__ = "walkloud, Christopher Körber"
__version__ = "0.1.0"

from os import path

from setuptools import setup, find_packages

CWD = path.abspath(path.dirname(__file__))

with open(path.join(CWD, "README.md"), encoding="utf-8") as inp:
    LONG_DESCRIPTION = inp.read()

with open(path.join(CWD, "requirements.txt"), encoding="utf-8") as inp:
    REQUIREMENTS = [el.strip() for el in inp.read().split(",")]

setup(
    name="nucleon_elastic_FF",
    version=__version__,
    description="Module to massage HDF5 correlator files into smaller pieces",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/callat-qcd/nucleon_elastic_FF",
    author=__author__,
    author_email="ckoerber@berkeley.edu",
    keywords=["HDF5", "LQCD", "FFT", "CUDA"],
    packages=find_packages(exclude=["docs", "tests", "tmp_a09m310_e_scripts"]),
    install_requires=REQUIREMENTS,
    entry_points={
        "console_scripts": [
            "h5eq=nucleon_elastic_ff.data.scripts.h5eq:main",
            "nucelff=nucleon_elastic_ff.data.scripts.nucelff:main",
            "h5fft=nucleon_elastic_ff.data.scripts.fft:main",
        ]
    },
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
)
