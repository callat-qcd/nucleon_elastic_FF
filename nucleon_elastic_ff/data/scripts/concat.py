"""Script for concatenating correlator data
"""
from typing import List
from typing import Dict
from typing import Optional

import os
import re

import h5py
import numpy as np

from nucleon_elastic_ff.utilities import set_up_logger
from nucleon_elastic_ff.utilities import find_all_files
from nucleon_elastic_ff.utilities import has_match

from nucleon_elastic_ff.data.h5io import get_dsets
from nucleon_elastic_ff.data.h5io import create_dset

from nucleon_elastic_ff.data.scripts.utilities import group_files
from nucleon_elastic_ff.data.scripts.utilities import parse_dset_address
from nucleon_elastic_ff.data.scripts.utilities import assert_patterns_present


LOGGER = set_up_logger("nucleon_elastic_ff")


def concat_dsets(  # pylint: disable=R0913, R0914
    files: List[str],
    out_file: str,
    axis: int = 0,
    dset_replace_patterns: Optional[Dict[str, str]] = None,
    ignore_containers: Optional[List[str]] = None,
    overwrite: bool = False,
):
    """Reads h5 files and exports the contatenation of datasets across files.

    Each group in the file list will be contatenated over files.
    Files are sorted before concatenation.

    Also the contatenation meta info is stored in the resulting output file in the `meta`
    attribute of `local_current`.

    .. note:: Suppose you pass two h5 files ``files = ["file1.h5", "file2.h5"]``.
        to write to the out file ``out_file = "out.h5"``. Lets assume the dset structure
        is as follows

        .. code-block:: bash

            file1.h5
            /x1y1
            /x1y2

        and also

        .. code-block:: bash

            file2.h5
            /x1y1
            /x1y2

        .. code-block:: bash

            out.h5
            /x1y1
            /x1y2

        where the dset ``x1y1`` is ``np.append(file1.h5/x1y1, file2.h5/x1y1, axis=axis)``
        and so on.

        **Arguments**
            files: List[str]
                List of h5 file address which will be read into memory and averaged over.

            out_file: str
                The name of the file which will contain the averages.

            axis: Optional[int] = 0
                The axis to concatenate over.

            dset_replace_patterns: Dict[str, str]
                A map for how dsets in the input files are used to write to the output
                file. The routine only concatenates over dsets which match all keys of
                dset_replace_patterns.

            ignore_containers: Optional[List[str]] = None
                Ignores the following h5 containers (groups or dsets) when concatinating.
                (dont write them at all).

            overwrite: bool = False
                Overwrite existing files.
    """
    ignore_containers = ignore_containers or []
    dset_replace_patterns = dset_replace_patterns or {}

    dsets_list = {}
    dsets_meta = {}

    LOGGER.info(
        "Starting concatenating over `%d` files with hdf5 group/dset substitutions",
        len(files),
    )
    for pat, subs in dset_replace_patterns.items():
        LOGGER.info("\t'%s' = '%s'", pat, subs)
    LOGGER.info("The export file will be called `%s`", out_file)

    LOGGER.info("Start parsing files")
    for file in np.sort(files):
        LOGGER.debug("Parsing file `%s`", file)
        with h5py.File(file, "r") as h5f:

            for key, val in get_dsets(
                h5f, load_dsets=False, ignore_containers=ignore_containers
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
                meta += "&".join([f"{kkey}=={vval}" for kkey, vval in meta_info.items()])

                if out_grp in dsets_list:
                    dsets_list[out_grp] += [val[()]]
                    dsets_meta[out_grp] += ("\n" + meta) if meta else ""
                else:
                    dsets_list[out_grp] = [val[()]]
                    dsets_meta[out_grp] = meta

    LOGGER.info("Writing `%d` dsets to `%s`", len(dsets_list), out_file)
    with h5py.File(out_file) as h5f:
        for key, dset_list in dsets_list.items():
            LOGGER.debug(
                "Concatinating dsets `%s` (list of %d dsets) with meta info:\n\t`%s`",
                key,
                len(dset_list),
                dsets_meta[key],
            )
            create_dset(
                h5f, key, np.concatenate(dset_list, axis=axis), overwrite=overwrite
            )
            h5f[key].attrs["meta"] = dsets_meta[key]


def concatenate(  # pylint: disable=R0913, R0914
    root: str,
    concatenation_pattern: Dict[str, str],
    axis: int = 0,
    file_match_patterns: Optional[List[str]] = None,
    dset_replace_patterns: Optional[Dict[str, str]] = None,
    expected_file_patterns: Optional[List[str]] = None,
    ignore_containers: Optional[List[str]] = None,
    overwrite: bool = False,
):
    """Recursively scans directory for files and concatinates them.

    Finds files and all files which will be considered for grouping and feeds them to
    ``concat_dsets``.

    The concatinated dset will be ordered according to the file names.

    **Arguments**
        root: str
            Root directory to recursively scan for files to concatinate.

        concatenation_pattern: Dict[str, str]
            The regex patterns to use for consider for concatinating.
            The input files must match the key which will be replaced by the value.
            Only files with similar pattern will be concatinated.

        axis: int = 0
            The axis to concatinate over.

        file_match_patterns: Optional[List[str]] = None
            The regex patterns which file must match in order to be found.
            This list is extended by concationation pattern keys.

        dset_replace_patterns: Optional[Dict[str, str]] = None
            The patterns for dsets to be replaced after concationaion.

        expected_file_patterns: Optional[List[str]] = None
            Adds expected regex patterns to file filter patterns.
            After files have been filtered and grouped, checks if all strings in this
            list are present in the file group.
            If not exactly all sources are found in the group, raises AssertionError.

        ignore_containers: Optional[List[str]] = None
            Ignore certain h5 groups and dsets and not concat them
            (dont write them at all).

        overwrite: bool = False
            Overwrite existing sliced files.
    """
    LOGGER.info("Running concatenate")

    file_match_patterns = file_match_patterns or []

    files = find_all_files(
        root,
        file_patterns=file_match_patterns + list(concatenation_pattern.keys()),
        exclude_file_patterns=list(concatenation_pattern.values()),
        match_all=True,
    )
    if expected_file_patterns is not None:
        files = [file for file in files if has_match(file, expected_file_patterns)]
    n_expected_sources = len(expected_file_patterns)

    file_groups = {}
    for file in files:
        new_file_name = file
        for pattern, replacement in concatenation_pattern.items():
            new_file_name = re.sub(pattern, replacement, new_file_name)
        if new_file_name in file_groups:
            file_groups[new_file_name] += [file]
        else:
            file_groups[new_file_name] = [file]

    for file_group in file_groups.values():
        out_file = file_group[0]

        if n_expected_sources:
            if len(file_group) != n_expected_sources:
                raise AssertionError(
                    "Expected %d sources in one average group but only received %d"
                    % (n_expected_sources, len(file_group))
                )

        if expected_file_patterns:
            assert_patterns_present(expected_file_patterns, file_group)

        for pat, subs in concatenation_pattern.items():
            out_file = re.sub(pat, subs, out_file)

        base_dir = os.path.dirname(out_file)
        if not os.path.exists(base_dir):
            LOGGER.info("Creating `%s`", base_dir)
            os.makedirs(base_dir)

        concat_dsets(
            file_group,
            out_file,
            axis=axis,
            dset_replace_patterns=dset_replace_patterns,
            ignore_containers=ignore_containers,
            overwrite=overwrite,
        )


def main():
    """Command line run script for concat module
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Interface for `concatenate`."
        " Recursively scans directory for files and concatinates them."
        " The concatinated dset will be ordered according to the file names."
    )
    parser.add_argument(
        "root",
        type=str,
        help="Root directory to recursively scan for files to concatenate.",
    )
    parser.add_argument(
        "--concatenation-group",
        "-g",
        type=str,
        help="The regex patterns to use for consider for concatinating."
        " The input files must match this string."
        " Only files with similar pattern will be concatinated.",
    )
    parser.add_argument(
        "--concatenation-replacement",
        "-r",
        type=str,
        default="",
        help="The name for replacing matched patterns (`concatenation-group` flag)."
        " E.g. `file_{concatenation-group}.h5 -> file_{concatenation-replacement}.h5`."
        " [default='%(default)s']",
    )
    parser.add_argument(
        "--axis",
        "-a",
        type=int,
        default=0,
        help="The axis to concatenate over. [default='%(default)s']",
    )
    parser.add_argument(
        "--file-match-patterns",
        "-m",
        type=str,
        nargs="+",
        default=None,
        help="The regex patterns which file must match in order to be found"
        " (space separted list)."
        " This list is extended by the concatenation-group flag."
        " [default='%(default)s']",
    )
    parser.add_argument(
        "--expected-file-patterns",
        "-e",
        type=str,
        nargs="+",
        default=None,
        help="Adds expected regex patterns to file filter patterns."
        " (space separted list)."
        " After files have been filtered and grouped, checks if all strings in this"
        " list are present in the file group."
        " If not exactly all sources are found in the group, raises AssertionError."
        " [default='%(default)s']",
    )
    parser.add_argument(
        "--overwrite",
        "-f",
        action="store_true",
        default=False,
        help="Overwrite hdf5 files if they already exist. [default=%(default)s]",
    )
    args = parser.parse_args()
    concatenate(
        root=args.root,
        concatenation_pattern={args.concatenation_group: args.concatenation_replacement},
        axis=args.axis,
        file_match_patterns=args.file_match_patterns,
        dset_replace_patterns=None,
        expected_file_patterns=args.expected_file_patterns,
        ignore_containers=None,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
