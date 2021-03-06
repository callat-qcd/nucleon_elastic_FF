"""Script for comparing two hdf5 files
"""
from argparse import ArgumentParser

from nucleon_elastic_ff.data.h5io import assert_h5files_equal
from nucleon_elastic_ff.data.h5io import assert_h5dsets_equal

PARSER = ArgumentParser(
    description="Compare two hdf5 files."
    " Checks if for each entry `|acutal - expected| < atol + rtol * |expected|`"
    " If one or both of `dset-actual`|`dset-expected` is given, just compares dsets."
    " (Uses the same dset for both if just one is given.)"
)
PARSER.add_argument("actual", type=str, help="Address to actual file.")
PARSER.add_argument("expected", type=str, help="Address to expected file.")
PARSER.add_argument(
    "--atol",
    "-a",
    type=float,
    default=0.0,
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
PARSER.add_argument(
    "--dset-actual",
    type=str,
    default=None,
    help="Dset of actual file to use for comparison.",
)
PARSER.add_argument(
    "--dset-expected",
    type=str,
    default=None,
    help="Dset of expected file to use for comparison.",
)


def main():
    """Compare two hdf5 files
    """
    args = PARSER.parse_args()

    if args.dset_actual or args.dset_expected:
        assert_h5dsets_equal(
            args.actual,
            args.expected,
            dset_actual=args.dset_actual or args.dset_expected,
            dset_expected=args.dset_expected or args.dset_actual,
            atol=args.atol,
            rtol=args.rtol,
        )

    else:
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
