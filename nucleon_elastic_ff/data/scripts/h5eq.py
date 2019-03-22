"""Script for comparing two hdf5 files
"""
from argparse import ArgumentParser

from nucleon_elastic_ff.data.h5io import assert_h5files_equal

PARSER = ArgumentParser(description="Compare two hdf5 files")
PARSER.add_argument("actual", type=str, help="Address to actual file.")
PARSER.add_argument("expected", type=str, help="Address to expected file.")
PARSER.add_argument(
    "--atol",
    "-a",
    type=float,
    default=1.0e-7,
    help="Absolute comparison difference (default = [%(default)s]).",
)
PARSER.add_argument(
    "--rtol",
    "-r",
    type=float,
    default=1.0e-7,
    help="Absolute comparison difference (default = [%(default)s]).",
)
PARSER.add_argument(
    "--group-actual",
    type=str,
    default=None,
    help="Group of actual file to use for comparison (if None compare all).",
)
PARSER.add_argument(
    "--group-expected",
    type=str,
    default=None,
    help="Group of expected file to use for comparison (if None compare all).",
)


def main():
    """Compare two hdf5 files
    """
    args = PARSER.parse_args()

    assert_h5files_equal(
        args.actual,
        args.expected,
        atol=args.atol,
        rtol=args.rtol,
        group_actual=args.group_actual,
        group_expected=args.group_expected,
    )
    print("[+] Files are equal!")


if __name__ == "__main__":
    main()
