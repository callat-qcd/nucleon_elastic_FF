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
    "--tslice-fact",
    "-t",
    type=float,
    default=None,
    help="Interface for controlling factor for determening sclicing size."
    " E.g., if a a file has NT = 48 and tslice_fact is 0.5, only time"
    " slices from 0 to 23 are exported to the output file. Note that the source"
    " location is shifted before slicing. If this argument is specified,"
    " the code looks for files which match `spec_4D`",
)
PARSER.add_argument(
    "--average",
    "-a",
    action="store_true",
    default=False,
    help="Average time sliced files over different sources."
    " Looks for `formfac_4D_tslice` files."
    " See `nucleon_elastic_ff.data.scripts.average` for more info.",
)
PARSER.add_argument(
    "--average-spec",
    action="store_true",
    default=False,
    help="Average time sliced files over different sources, spin and parity."
    " Similar to `average` flag but looks for `spec_4D_tslice` files."
    " See `nucleon_elastic_ff.data.scripts.spec_average` for more info.",
)

PARSER.add_argument(
    "--overwrite",
    "-f",
    action="store_true",
    default=False,
    help="Overwrite hdf5 files if they already exist.",
)

PARSER.add_argument(
    "--n-expected-sources",
    "-n",
    type=int,
    default=None,
    help="Option passed to average sources. If specified, raise error if number of"
    " sources in one average group is different than specified.",
)


def main():
    """Runs src average and or tslice.
    """
    args = PARSER.parse_args()
    LOGGER.info("Running nucleon_elastic_ff scripts")
    LOGGER.info("Full log can be found in `nucleon_elastic_ff.log`")

    if args.slice:
        if args.tslice_fact is not None:
            tslice.tslice(
                args.root,
                name_input="spec_4D",
                name_output="spec_4D_tslice",
                overwrite=args.overwrite,
                tslice_fact=args.tslice_fact,
                dset_patterns=["4D_correlator/x[0-9]+_y[0-9]+_z[0-9]+_t[0-9]+"],
            )

        else:
            tslice.tslice(args.root, overwrite=args.overwrite)

    if args.average:
        average.source_average(
            args.root,
            overwrite=args.overwrite,
            n_expected_sources=args.n_expected_sources,
        )

    if args.average_spec:
        average.spec_average(
            args.root,
            overwrite=args.overwrite,
            n_expected_sources=args.n_expected_sources,
        )


if __name__ == "__main__":
    main()
