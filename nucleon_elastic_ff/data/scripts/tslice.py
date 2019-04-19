"""Script for time slicing correlator data
"""
from typing import Tuple
from typing import List
from typing import Optional

import os
import re

import numpy as np
import h5py

from nucleon_elastic_ff.utilities import set_up_logger
from nucleon_elastic_ff.utilities import find_all_files
from nucleon_elastic_ff.utilities import has_match

from nucleon_elastic_ff.data.h5io import get_dsets
from nucleon_elastic_ff.data.h5io import create_dset

from nucleon_elastic_ff.data.parsing import parse_t_info
from nucleon_elastic_ff.data.parsing import parse_file_info

from nucleon_elastic_ff.data.arraymanip import shift_array

LOGGER = set_up_logger("nucleon_elastic_ff")


def tslice(  # pylint: disable=R0913
    root: str,
    name_input: str = "formfac_4D",
    name_output: str = "formfac_4D_tslice",
    overwrite: bool = False,
    tslice_fact: Optional[float] = None,
    dset_patterns: List[str] = ("local_current",),
):
    """Recursively scans dir for files, slices in time and shifts in all directions.

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

        tslice_fact: Optional[float] = None
            User interface for controlling factor for determening sclicing size.
            E.g., if a a file has ``NT = 48`` and ``tslice_fact`` is 0.5, only time
            slices from 0 to 23 are exported to the output file. Note that the source
            location is shifted before slicing.

        dset_patterns: List[str] = ("local_current",),
            Pattern dsets must matched in order to be sliced.

    **Raises**
        ValueError:
            If ``tslice_fact`` is not ``None`` but one is able to parse ``tsep``
            information from the file string. This is a safeguard against accidentally
            slicing files which shall not be sliced.
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

    for n_file, file_address in enumerate(all_files):
        LOGGER.info("--- File %d of %d ---", n_file + 1, len(all_files))
        file_address_out = file_address.replace(name_input, name_output)
        if not os.path.exists(os.path.dirname(file_address_out)):
            os.makedirs(os.path.dirname(file_address_out))
        slice_file(
            file_address,
            file_address_out,
            overwrite=overwrite,
            tslice_fact=tslice_fact,
            dset_patterns=dset_patterns,
        )

    LOGGER.info("Done")


def slice_file(  # pylint: disable=R0914
    file_address_in: str,
    file_address_out: str,
    overwrite: bool = False,
    tslice_fact: Optional[float] = None,
    dset_patterns: List[str] = ("local_current",),
):
    """Reads input file and writes time-sliced data to output file.

    This methods scans all datasets within the file.
    If a data set has "local_current" in its name it is sliced in its time components.
    The slicing info is inferred by the group name (see `parse_t_info`).
    Also the slicing meta info is stored in the resulting output file in the "meta_info"
    group (same place as "local_current").

    **Arguments**
        file_address_in: str
            Address of the to be scanned and sliced HDF5 file.

        file_address_out: str
            Address of the output HDF5 file.

        overwrite: bool = False
            Overwrite existing sliced file.

        tslice_fact: Optional[float] = None
            User interface for controlling factor for determening sclicing size.
            E.g., if a a file has ``NT = 48`` and ``tslice_fact`` is 0.5, only time
            slices from 0 to 23 are exported to the output file. Note that the source
            location is shifted before slicing.

        dset_patterns: List[str] = ("local_current",),
            Pattern dsets must matched in order to be sliced.

    **Raises**
        ValueError:
            If ``tslice_fact`` is not ``None`` but one is able to parse ``tsep``
            information from the file string. This is a safeguard against accidentally
            slicing files which shall not be sliced.
    """
    LOGGER.info("Sclicing\n\t  `%s`\n\t->`%s`", file_address_in, file_address_out)

    with h5py.File(file_address_in, "r") as h5f:
        dsets = get_dsets(h5f, load_dsets=False)

        with h5py.File(file_address_out) as h5f_out:
            for name, dset in dsets.items():

                if has_match(name, dset_patterns, match_all=True):
                    LOGGER.debug("Start slicing dset `%s`", name)

                    pattern = ".*(?:proton|neutron)(?:_(?P<parity>np))?"
                    match = re.match(pattern, name)
                    if not match:
                        raise ValueError("Could not infer parity of dset `%s`" % name)
                    negative_parity = match.groupdict()["parity"] == "np"

                    t_info = parse_t_info(name)
                    t_info["nt"] = dset.shape[0]
                    if tslice_fact is not None:
                        if "tsep" in t_info:
                            raise ValueError(
                                "Found `tsep = %s` in file `%s`"
                                " but user specified `tslice_fact`. Abort."
                                % (t_info["tsep"], name)
                            )
                        else:
                            t_info["tsep"] = int(t_info["nt"] * tslice_fact)

                    if negative_parity and t_info["tsep"] > 0:
                        t_info["tsep"] *= -1

                    LOGGER.debug("\tExtract temporal info `%s`", t_info)

                    meta = dset.attrs.get("meta", None)
                    meta = str(meta) + "&" if meta else ""
                    meta += "&".join([f"{key}=={val}" for key, val in t_info.items()])

                    slice_index, slice_fact = get_t_slices(**t_info)
                    slice_fact = slice_fact.reshape(
                        [t_info["tsep"] + 1] + [1] * (len(dset.shape) - 1)
                    )
                    out = slice_fact * dset[()][slice_index]

                    LOGGER.debug("\tShifting to source origin")
                    info = parse_file_info(file_address_in, convert_numeric=True)
                    for axis, key in enumerate(["z", "y", "x"]):
                        LOGGER.debug("\t\t %s -> %s %+d", key, key, -info[key])
                        out = shift_array(out, -info[key], axis=axis + 1)

                else:
                    out = dset[()]

                create_dset(h5f_out, name, out, overwrite=overwrite)


def get_t_slices(  # pylint: disable=C0103
    t0: int, tsep: int, nt: int
) -> Tuple[List[int], np.ndarray]:
    """Returns range `[t0, t0 + tsep + step]` where `step` is defined by sign of `tsep`.

    List elements are counted modulo the maximal time extend nt.
    This function returns the new indices and the factor associated with the indices.
    E.g., if ``tsep`` is negative (T is applied), all entries but ``t0`` are multiplied
    by minus one. Also, entries which hop the boundaries are multiplied by minus one.

    **Arguments**
        t0: int
            Start index for slicing.

        tsep: int
            Seperation for slicing.

        nt: int
            Maximum time slice.
    """
    step = tsep // abs(tsep)

    actual_t = range(t0, t0 + tsep + step, step)
    index_t = [ind % nt for ind in actual_t]

    fact = np.ones(len(index_t), dtype=int)
    for n, t in enumerate(actual_t):
        if t < 0 or t >= nt:
            fact[n] *= -1

        if tsep < 0 and t != t0:
            fact[n] *= -1

    return index_t, fact
