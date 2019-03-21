"""Script for time averaging correlator data
"""
from typing import List
from typing import Union
from typing import Dict
from typing import Tuple

import os
import re

import h5py

from nucleon_elastic_ff.utilities import set_up_logger
from nucleon_elastic_ff.utilities import find_all_files
from nucleon_elastic_ff.utilities import has_match

from nucleon_elastic_ff.data.parsing import parse_file_info

from nucleon_elastic_ff.data.h5io import get_dsets
from nucleon_elastic_ff.data.h5io import create_dset

from nucleon_elastic_ff.data.arraymanip import average_arrays


LOGGER = set_up_logger("nucleon_elastic_ff")


def get_groups(
    all_files: List[str], keys: List[str]
) -> Dict[Dict[str, Union[int, float, str]], str]:
    """Collects files by properties which are not allowed to differ.
    """
    LOGGER.debug("Collecting groups")
    groups = {}
    for file in all_files:
        info = parse_file_info(file, convert_numeric=False)
        for key in keys:
            info.pop(key)

        info_str = "&".join([f"{key}={val}" for key, val in info.items()])
        if info_str in groups:
            groups[info_str].append(file)
        else:
            LOGGER.debug("Found group %s", info_str)
            groups[info_str] = [file]

    return groups


def average_group(
    files: List[str],
    file_replace_pattern: Tuple[str, str],
    group_replace_pattern: Tuple[str, str],
    overwrite: bool = False,
):
    """Reads h5 files and exports the average of datasets across files.
    """
    dsets = {}
    for file in files:
        with h5py.File(file, "r") as h5f:
            file_dsets = get_dsets(h5f, load_dsets=True)

            for key, val in file_dsets.items():
                if key in dsets:
                    dsets[key].append(val)
                else:
                    dsets[key] = [val]

    out_file = re.sub(file_replace_pattern[0], file_replace_pattern[1], files[0])
    with h5py.File(out_file) as h5f:
        for dset_address, val in dsets.items():
            avg_address = re.sub(
                group_replace_pattern[0], group_replace_pattern[1], dset_address
            )

            if has_match(avg_address, ["local_current"]):
                avg = average_arrays(val)
                create_dset(h5f, avg_address, avg, overwrite=overwrite)
                for n, file in enumerate(files):
                    h5f[avg_address].attrs[f"avg_file_{n}"] = file


def average(  # pylint: disable=R0913
    root: str,
    avg_over_keys: List[str],
    file_locate_pattern: str,
    file_replace_pattern: Tuple[str, str],
    group_replace_pattern: Tuple[str, str],
    overwrite: bool = False,
):
    """Recursively scans directory for files and averages matches which over specified
    component.

    The input files must be h5 files (ending with ".h5") and must have `name_input`
    in their file name. Files which have `name_output` as name are excluded.
    Also, this routine ignores exporting to files which already exist.

    **Arguments**
        root: str
            The directory to look for files.

        avg_over_keys: List[str]
            The keys which are allowed to differ when deciding which files belong in one
            group.

        name_input: str
            Files must match this pattern to be submitted for averaging.

        name_output: str
            Files must not match this pattern to be submitted for averaging.
            Also the averaged output files will have the input name replaced by the
            output name. This also includes directory names.

        overwrite: bool = False
            Overwrite existing sliced files.

    """
    LOGGER.info("Starting averaging files")
    LOGGER.info("Looking into `%s`", root)
    LOGGER.info(
        "Locating files matching pattern `%s` and `%s` but ignoring files matching `%s`",
        file_locate_pattern,
        file_replace_pattern[0],
        file_replace_pattern[1],
    )

    all_files = find_all_files(
        root,
        file_patterns=[file_locate_pattern + r".*\.h5$", file_replace_pattern[0]],
        exclude_file_patterns=[file_replace_pattern[1]],
        match_all=True,
    )
    if not overwrite:
        all_files = [
            file
            for file in all_files
            if not os.path.exists(
                re.sub(file_replace_pattern[0], file_replace_pattern[1], file)
            )
        ]
    LOGGER.info(
        "Found %d files which match the pattern%s",
        len(all_files),
        " " if overwrite else " (and do not exist)",
    )

    LOGGER.info(
        "Now averaging over files which have same pars besides their values for `%s`",
        avg_over_keys,
    )

    groups = get_groups(all_files, avg_over_keys)
    LOGGER.info("Found %d groups", len(groups))
    for group, files in groups.items():
        LOGGER.debug("Averaging over group %s", group)
        average_group(
            files, file_replace_pattern, group_replace_pattern, overwrite=overwrite
        )

    LOGGER.info("Done")


def source_average(  # pylint: disable=R0913
    root: str,
    avg_over_keys: Tuple[str] = ("x", "y", "z", "t"),
    file_locate_pattern: str = "formfac_4D_tslice",
    file_replace_pattern: str = ("x[0-9]+y[0-9]+z[0-9]+t[0-9]+", "src_avg"),
    group_replace_pattern: str = ("x[0-9]+_y[0-9]+_z[0-9]+_t[0-9]+", "src_avg"),
    overwrite: bool = False,
):
    """Recursively scans directory for files and averages matches which over specified
    component.

    The input files must be h5 files (ending with ".h5") and must have `name_input`
    in their file name. Files which have `name_output` as name are excluded.
    Also, this routine ignores exporting to files which already exist.

    **Arguments**
        root: str
            The directory to look for files.

        file_locate_pattern: str = "formfac_4D"
            Files must match this pattern to be submitted for slicing.

        name_output: str = "formfac_4D_tslice"
            Files must not match this pattern to be submitted for slicing.
            Also the sliced output files will have the input name replaced by the output
            name. This also includes directory names.

        overwrite: bool = False
            Overwrite existing sliced files.

    """
    average(
        root,
        avg_over_keys,
        file_locate_pattern,
        file_replace_pattern,
        group_replace_pattern,
        overwrite=overwrite,
    )


def t0_average(  # pylint: disable=R0913
    root: str,
    avg_over_keys: Tuple[str] = ("t0",),
    file_locate_pattern: str = "formfac_4D_tslice.*src_avg",
    file_replace_pattern: str = ("src_avg", "src_t0_avg"),
    group_replace_pattern: str = (r"t0_[\+\-0-9]+", "t0_avg"),
    overwrite: bool = False,
):
    """Recursively scans directory for files and averages matches which over specified
    component.

    The input files must be h5 files (ending with ".h5") and must have `name_input`
    in their file name. Files which have `name_output` as name are excluded.
    Also, this routine ignores exporting to files which already exist.

    **Arguments**
        root: str
            The directory to look for files.

        file_locate_pattern: str = "formfac_4D_tslice.*src_avg"
            Files must match this pattern to be submitted for slicing.

        name_output: str = "src_t0_avg"
            Files must not match this pattern to be submitted for slicing.
            Also the sliced output files will have the input name replaced by the output
            name. This also includes directory names.

        overwrite: bool = False
            Overwrite existing sliced files.

    """
    average(
        root,
        avg_over_keys,
        file_locate_pattern,
        file_replace_pattern,
        group_replace_pattern,
        overwrite=overwrite,
    )
