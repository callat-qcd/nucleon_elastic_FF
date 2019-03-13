"""Script for time slicing correlator data
"""
from typing import List

import os

import h5py

from nucleon_elastic_ff.utilities import set_up_logger
from nucleon_elastic_ff.utilities import find_all_files
from nucleon_elastic_ff.utilities import has_match

from nucleon_elastic_ff.data.h5io import get_dsets
from nucleon_elastic_ff.data.h5io import create_dset

from nucleon_elastic_ff.data.parsing import parse_t_info

from nucleon_elastic_ff.data.arraymanip import slice_array


LOGGER = set_up_logger("nucleon_elastic_ff")


def tslice(
    root: str,
    name_input: str = "formfac_4D",
    name_output: str = "formfac_4D_tslice",
    overwrite: bool = False,
):
    """Recursively scans directory for files and slices matches in time direction.

    The input files must be h5 files (ending with ".h5") and must have `name_input`
    in their file name. Files which have `name_output` as name are excluded.
    Also, this routine ignores exporting to files which already exist.
    Once all files are fixed, this routine calls `slice_file` on each file.

    **Arguments**
        root: str
            The directory to look for files.

        name_input: str = "formfac_4D"
            Files must match this pattern to be submitted for slicing.

        name_output: str = "formfac_4D_tslice"
            Files must not match this pattern to be submitted for slicing.
            Also the sliced output files will have the input name replaced by the output
            name. This also includes directory names.

        overwrite: bool = False
            Overwrite existing sliced files.

    """
    LOGGER.info("Starting slicing of files")
    LOGGER.info("Looking into `%s`", root)
    LOGGER.info(
        "Using naming convention `%s` -> `%s` (for sliced data) ",
        name_input,
        name_output,
    )

    all_files = find_all_files(
        root,
        file_patterns=[name_input + r".*\.h5$"],
        exclude_file_patterns=[name_output],
    )
    if not overwrite:
        all_files = [
            file
            for file in all_files
            if not os.path.exists(file.replace(name_input, name_output))
        ]
    LOGGER.info(
        "Found %d files which match the pattern%s",
        len(all_files),
        " " if overwrite else " (and do not exist)",
    )

    for file_address in all_files:
        file_address_out = file_address.replace(name_input, name_output)
        if not os.path.exists(os.path.dirname(file_address_out)):
            os.mkdir(os.path.dirname(file_address_out))
        LOGGER.info("-> `%s`", file_address)
        slice_file(file_address, file_address_out, overwrite=overwrite)

    LOGGER.info("Done")


def slice_file(file_address_in: str, file_address_out: str, overwrite: bool = False):
    """Reads input file and writes time-sliced data to output file.

    This methods scans all datasets within the file.
    If a data set has "local_current" in its name it is sliced in its time components.
    The slicing info is inferred by the group name (see `parse_t_info`) and cut according
    using `slice_array`.
    Also the slicing meta info is stored in the resulting output file in the "meta_info"
    group (same place as "local_current").

    **Arguments**
        file_address_in: str
            Address of the to be scanned and sliced HDF5 file.

        file_address_out: str
            Address of the output HDF5 file.

        overwrite: bool = False
            Overwrite existing sliced file.
    """
    with h5py.File(file_address_in, "r") as h5f:
        dsets = get_dsets(h5f, load_dsets=False)

        with h5py.File(file_address_out) as h5f_out:
            for name, dset in dsets.items():

                if has_match(name, ["local_current"]):
                    LOGGER.debug("Start slicing `%s`", name)
                    t_info = parse_t_info(name)
                    t_info["nt"] = dset.shape[0]
                    meta_name = name.replace("local_current", "meta_info")
                    LOGGER.debug("Extract temporal info `%s`", t_info)
                    for key, val in t_info.items():
                        create_dset(
                            h5f_out,
                            os.path.join(meta_name, key),
                            val,
                            overwrite=overwrite,
                        )

                    slice_index = get_t_slices(**t_info)
                    out = slice_array(dset[()], slice_index)

                else:
                    out = dset[()]

                create_dset(h5f_out, name, out, overwrite=overwrite)


def get_t_slices(t0: int, tsep: int, nt: int) -> List[int]:  # pylint: disable=C0103
    """Returns range `[t0, t0 + tsep + step]` where `step` is defined by sign of `tsep`.

    List elements are counted modulo the maximal time extend nt.

    **Arguments**
        t0: int
            Start index for slicing.

        tsep: int
            Seperation for slicing.

        nt: int
            Maximum time slice.
    """
    step = tsep // abs(tsep)
    return [ind % nt for ind in range(t0, t0 + tsep + step, step)]
