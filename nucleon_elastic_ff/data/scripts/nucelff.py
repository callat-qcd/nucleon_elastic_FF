"""Main interface to data scripts
"""
from argparse import ArgumentParser

from nucleon_elastic_ff.utilities import set_up_logger

from nucleon_elastic_ff.data.scripts import average
from nucleon_elastic_ff.data.scripts import tslice

LOGGER = set_up_logger("nucleon_elastic_ff")

PARSER = ArgumentParser(description="Run nucleon_elastic_ff scripts.")
PARSER.add_argument(
    "root", type=str, help="Root directory to look for files to slice or average."
)

PARSER.add_argument(
    "--slice",
    "-s",
    action="store_true",
    default=False,
    help="Slice files in time direction and shift source to origin."
    " Also multiply negative parity by minus one when slicing time."
    "See `nucleon_elastic_ff.data.scripts.tslice` for more info.",
)
PARSER.add_argument(
    "--average",
    "-a",
    action="store_true",
    default=False,
    help="Average time sliced files over different sources."
    "See `nucleon_elastic_ff.data.scripts.average` for more info.",
)

PARSER.add_argument(
    "--overwrite",
    "-f",
    action="store_true",
    default=False,
    help="Overwrite hdf5 files if they already exist.",
)


def main():
    """Runs src average and or tslice.
    """
    args = PARSER.parse_args()
    LOGGER.info("Running nucleon_elastic_ff scripts")
    LOGGER.info("Full log can be found in `nucleon_elastic_ff.log`")

    if args.tslice:
        tslice.tslice(args.root, overwrite=args.overwrite)

    if args.average:
        average.source_average(args.root, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
