"""Script for time averaging correlator data
"""
import h5py

import numpy as np

from nucleon_elastic_ff.utilities import set_up_logger

from nucleon_elastic_ff.data.h5io import get_dsets
from nucleon_elastic_ff.data.h5io import create_dset

LOGGER = set_up_logger("nucleon_elastic_ff")


def dset_migrate(  # pylint: disable=R0914, R0913
    inp_file: str, out_file: str, atol: float = 0.0, rtol: float = 1.0e-8,
):
    """Reads h5 file and copies dsets from first into second.

    If dset exists, they are compared first (`|inp-out|<=atol + rtol*|out|`).
    If they do not agree the user will be warned about that.
    Only dsets which don't contain NaNs will be written. Dsets with NaNs raise an error.

        **Arguments**
            inp_file: str
                H5 file to copy dsets from.

            out_file: str
                H5 file to insert dsets into.

            atol:float
                Absolute tolarance for comparison.

            rtol:float
                Relative tolarance for comparison.


    """
    dsets_paths = {}
    n_dsets = {}
    dset_meta = {}

    LOGGER.info("Starting migration file `%s` into `%s`", inp_file, out_file)

    LOGGER.info("Start parsing files")

    with h5py.File(inp_file, "r") as h5i:
        dsets_inp = get_dsets(h5i, load_dsets=False)
        with h5py.File(out_file, "r+") as h5o:
            dsets_out = get_dsets(h5o, load_dsets=False)

            for key, dset in dsets_inp.items():
                LOGGER.debug("\tParsing dset `%s`", key)
                data = dset[()]
                meta = dset.attrs.get("meta", None)

                if np.isnan(data).any():
                    raise ValueError(
                        f"Dataset `{key}` in `{inp_file}` has NaN values. Aboard."
                    )

                if key not in dsets_out:
                    LOGGER.debug("\t\tWriting dset.")
                    create_dset(h5o, key, data, overwrite=False)
                    if meta is not None:
                        h5o[key].attrs["meta"] = meta
                else:
                    if not np.allclose(data, dsets_out[key][()], rtol=rtol, atol=atol):
                        LOGGER.warning(
                            "Dset `%s` in input file `%s` does not aggree with file `%s`"
                            " for atol=%g and rtol=%g",
                            key,
                            inp_file,
                            out_file,
                            atol,
                            rtol,
                        )
                    else:
                        LOGGER.debug("\t\tDset present and equal.")


def main():
    """Runs dset_migrate for argparse input
    """
    from argparse import ArgumentParser  # pylint: disable=C0415

    PARSER = ArgumentParser(description=dset_migrate.__doc__)
    PARSER.add_argument("inp_file", type=str, help="Address to input h5file.")
    PARSER.add_argument("out_file", type=str, help="Address to output h5file.")
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
    args = PARSER.parse_args()

    dset_migrate(args.inp_file, args.out_file, atol=args.atol, rtol=args.rtol)


if __name__ == "__main__":
    main()
