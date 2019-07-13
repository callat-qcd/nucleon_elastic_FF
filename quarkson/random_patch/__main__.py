"""Script to generates `n_int` integer in interval from `low` to `high` for given seed.
"""
from __future__ import print_function

import argparse

import __init__ as random

PARSER = argparse.ArgumentParser(
    description="Generates `n_int` integer in interval from"
    " `low` to `high` for given seed."
)
PARSER.add_argument("seed", help="The initializer value for the random seed.")
PARSER.add_argument(
    "-n", help="The number of to be generated integers.", default=10, type=int
)
PARSER.add_argument(
    "--low", help="The lower value of the of the interval.", default=0, type=int
)
PARSER.add_argument(
    "--high", help="The higher value of the of the interval.", default=10, type=int
)


def main(seed_init, n_int=10, low=0, high=10):
    """Generates `n_int` integer in interval from `low` to `high` for given seed.

    Arguments
    ---------
        seed_init:
            The initializer value for the random seed.

        n_int: int
            The number of to be generated integers.

        low, high: int
            The lower (higher) value of the of the interval.

    Returns
    -------
        integers: List
            The list of random integers.
    """
    random.seed(seed_init)
    return [random.randint(low, high) for _ in range(n_int)]


if __name__ == "__main__":
    ARGS = PARSER.parse_args()
    print(main(ARGS.seed, ARGS.n, ARGS.low, ARGS.high))
