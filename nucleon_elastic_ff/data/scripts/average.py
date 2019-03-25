"""Script for time averaging correlator data
"""
from typing import List
from typing import Union
from typing import Dict
from typing import Tuple
from typing import Optional

import re

import h5py

from nucleon_elastic_ff.utilities import set_up_logger
from nucleon_elastic_ff.utilities import find_all_files
from nucleon_elastic_ff.utilities import has_match

from nucleon_elastic_ff.data.parsing import parse_file_info

from nucleon_elastic_ff.data.h5io import get_dsets
from nucleon_elastic_ff.data.h5io import create_dset


LOGGER = set_up_logger("nucleon_elastic_ff")


def group_files(
    all_files: List[str], keys: List[str]
) -> Dict[Dict[str, Union[int, float, str]], str]:
    """Collects files by properties which are not allowed to differ.

    Parses the information from file names and groups them according to similar
    parameters.
    Labes in `keys` are allowed to differ.

    **Arguments**
        all_files: List[str]
            All files to group.

        keys: List[str]
            Keys which are allowed to differ.
    """
    LOGGER.info("Grouping %d files", len(all_files))
    LOGGER.info("Keys allowed to differ are: %s", keys)

    groups = {}
    for file in all_files:
        info = parse_file_info(file, convert_numeric=False)
        for key in keys:
            info.pop(key)

        info_str = "&".join([f"{key}={val}" for key, val in info.items()])
        if info_str in groups:
            groups[info_str].append(file)
        else:
            LOGGER.debug("Creating new group `%s`", info_str)
            groups[info_str] = [file]

    LOGGER.info("Created %d groups of files", len(groups))

    return groups


def parse_dset_address(
    address, dset_replace_patterns: Optional[Dict[str, str]] = None
) -> Tuple[str, Dict[str, str]]:
    """
    """

    out_grp = address
    meta_info = {}
    for pat, subs in dset_replace_patterns.items():
        out_grp = re.sub(pat, subs, out_grp)
        match = re.search(pat, address)
        if match:
            meta_info.update(match.groupdict())
    return out_grp, meta_info


def dset_avg(
    files: List[str],
    out_file: str,
    dset_replace_patterns: Dict[str, str],
    overwrite: bool = False,
):
    """Reads h5 files and exports the average of datasets across files.

    Each group in the file list will be averaged over files.
    """
    dsets_acc = {}
    n_dsets = {}
    dset_meta = {}

    LOGGER.info(
        "Starting averaging over `%d` files with hdf5 group/dset substitutions",
        len(files),
    )
    for pat, subs in dset_replace_patterns.items():
        LOGGER.info("\t'%s' = '%s'", pat, subs)
    LOGGER.info("The export file will be called `%s`", out_file)

    LOGGER.info("Start parsing files")
    for file in files:
        LOGGER.debug("Parsing file `%s`", file)
        with h5py.File(file, "r") as h5f:

            for key, val in get_dsets(
                h5f, load_dsets=False, ignore_containers=["meta_info"]
            ).items():
                LOGGER.debug("\tParsing dset `%s`", key)

                if not has_match(
                    key, list(dset_replace_patterns.keys()), match_all=True
                ):
                    LOGGER.debug("\t\tNo match")
                    continue

                out_grp, meta_info = parse_dset_address(key, dset_replace_patterns)
                LOGGER.debug("\t\tNew group:`%s`", out_grp)
                LOGGER.debug("\t\tMeta info: `%s`", meta_info)

                meta = val.attrs.get("meta", None)
                meta = str(meta) + "&" if meta else ""
                meta += "&".join(["{kkey}=={vval}" for kkey, vval in meta_info])

                if out_grp in dsets_acc:
                    dsets_acc[out_grp] += val[()]
                    n_dsets[out_grp] += 1
                    dset_meta[out_grp] += "\n" + meta
                else:
                    dsets_acc[out_grp] = val[()]
                    n_dsets[out_grp] = 1
                    dset_meta[out_grp] = meta

    LOGGER.info("Writing `%d` dsets to `%s`", len(dsets_acc), out_file)
    with h5py.File(out_file) as h5f:
        for key, acc in dsets_acc.items():
            LOGGER.debug(
                "Writing dset `%s` (average of %d dsets) with meta info:\n\t`%s`",
                key,
                n_dsets[key],
                dset_meta[key],
            )
            create_dset(h5f, key, acc / n_dsets[key], overwrite=overwrite)
            h5f[key].attrs["meta"] = dset_meta[key]


def source_average(root: str, overwrite: bool = False):  # pylint: disable=R0913
    """Recursively scans directory for files and averages matches which over specified
    component.

    The input files must be h5 files (ending with ".h5") and must have `name_input`
    in their file name. Files which have `name_output` as name are excluded.
    Also, this routine ignores exporting to files which already exist.

    **Arguments**
        root: str
            The directory to look for files.

        overwrite: bool = False
            Overwrite existing sliced files.

    """
    LOGGER.info("Running source average")

    avg_over_file_keys = ("x", "y", "z", "t")
    file_replace_pattern = {"x[0-9]+y[0-9]+z[0-9]+t[0-9]+": "src_avg"}
    dset_replace_pattern = {
        r"x(?P<x>[0-9]+)_y(?P<y>[0-9]+)_z(?P<z>[0-9]+)_t(?P<t>[0-9]+)": "src_avg",
        r"t0_(?P<t0>[0-9]+)_": "",
    }

    file_patterns = [r".*\.h5$", "formfac_4D_tslice"]
    file_patterns += list(file_replace_pattern.keys())

    files = find_all_files(
        root,
        file_patterns=file_patterns,
        exclude_file_patterns=list(file_replace_pattern.values()),
        match_all=True,
    )

    file_groups = group_files(files, keys=avg_over_file_keys)

    for file_group in file_groups.values():
        out_file = file_group[0]
        for pat, subs in file_replace_pattern.items():
            out_file = re.sub(pat, subs, out_file)

        dset_avg(file_group, out_file, dset_replace_pattern, overwrite=overwrite)
