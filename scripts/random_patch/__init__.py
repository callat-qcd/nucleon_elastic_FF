"""Bugfix module for consistent random integers between python2 and python3
"""
import os
import sys

from random import seed as py_seed
from random import randint as py_randint
from random import random

SYS_VER = sys.version_info.major


if int(os.environ["PYTHONHASHSEED"]) != 0:
    raise ValueError(
        "PYTHONHASHSEED is not zero."
        " This will cause inconsistent results when hashing with python 3"
    )


def seed(inp):
    """Sets the seed to the corresponding python 2 seed.

    Calls random.seed(inp, version=1) in python 3 and without version kwarg in python2.

    Arguments
    ---------
        inp:
            Input to `random.seed(inp)`
    """
    if SYS_VER == 2:
        py_seed(inp)
    else:
        py_seed(inp, version=1)


def randint(low, high):
    """Calls `random.randint(low, heigh)` in a compatible way for python 2 and 3.

    Calls `random() * (high - low + 1)` in python 3.

    Arguments
    ---------
        low, high: int
            The lower (higher) value of the of the interval.
    """
    if SYS_VER == 2:
        res = py_randint(low, high)
    else:
        res = int(random() * (high - low + 1) + low)
    return res
