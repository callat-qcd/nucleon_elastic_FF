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

from nucleon_elastic_ff.data.scripts.utilities import parse_dset_address
from nucleon_elastic_ff.data.scripts.utilities import assert_patterns_present


LOGGER = set_up_logger("nucleon_elastic_ff")


def concat_dsets(  # pylint: disable=R0913, R0914
    files: List[str],
    out_file: str,
    axis: int = 0,
    dset_replace_patterns: Optional[Dict[str, str]] = None,
    ignore_containers: Optional[List[str]] = None,
    write_unpaired_dsets: bool = False,
    overwrite: bool = False,
):
    """Reads h5 files and exports the contatenation of datasets across files.

    Each group in the file list will be contatenated over files.
    Files are concatenatinated in the order they are specified.

    Also the contatenation meta info is stored in the resulting output file in the `meta`
    attribute of `local_current`.

    .. note:: Suppose you pass two h5 files `files = ["file1.h5", "file2.h5"]`.
        to write to the out file `out_file = "out.h5"`. Lets assume the dset structure
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

        where the dset `x1y1` is
        `np.concatenate([file1.h5/x1y1, file2.h5/x1y1], axis=axis)`
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

            write_unpaired_dsets: bool = False
                Also write group of data sets where the number of data sets is fewer or
                more then the number of input files.
                Prints warning to stdout if numbers don't match in any case.

            overwrite: bool = False
                Overwrite existing files.
    """
    ignore_containers = ignore_containers or []
    dset_replace_patterns = dset_replace_patterns or {}

    dsets_paths = {}
    dsets_meta = {}

    n_files = len(files)

    LOGGER.info(
        "Starting concatenating over `%d` files with hdf5 group/dset substitutions",
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

                if out_grp in dsets_paths:
                    dsets_paths[out_grp].append((file, key))
                    dsets_meta[out_grp] += ("\n" + meta) if meta else ""
                else:
                    dsets_paths[out_grp] = [(file, key)]
                    dsets_meta[out_grp] = meta

    LOGGER.info("Writing `%d` dsets to `%s`", len(dsets_paths), out_file)
    with h5py.File(out_file) as h5f:
        for key, dset_path in dsets_paths.items():

            dset_list = []
            for (file, path) in dset_path:
                with h5py.File(file, "r") as h5fin:
                    dset_list.append(h5fin[path][()])

            if len(dset_list) == n_files:
                LOGGER.debug(
                    "Concatinating dsets `%s` (list of %d dsets)"
                    " with meta info:\n\t`%s`",
                    key,
                    len(dset_list),
                    dsets_meta[key],
                )
                create_dset(
                    h5f, key, np.concatenate(dset_list, axis=axis), overwrite=overwrite
                )
                h5f[key].attrs["meta"] = dsets_meta[key]
            else:
                LOGGER.warning(
                    "Expected %d but found %d dsets with same name for key `%s`",
                    n_files,
                    len(dset_list),
                    key,
                )
                if write_unpaired_dsets:
                    LOGGER.debug(
                        "Concatinating dsets `%s` (list of %d dsets)"
                        " with meta info:\n\t`%s`",
                        key,
                        len(dset_list),
                        dsets_meta[key],
                    )
                    create_dset(
                        h5f,
                        key,
                        np.concatenate(dset_list, axis=axis),
                        overwrite=overwrite,
                    )
                    h5f[key].attrs["meta"] = dsets_meta[key]
                else:
                    raise ValueError(
                        "Expected %d but found %d dsets with same name for key `%s`"
                        % (n_files, len(dset_list), key)
                    )


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
    `concat_dsets`.

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
            np.sort(file_group),
            out_file,
            axis=axis,
            dset_replace_patterns=dset_replace_patterns,
            ignore_containers=ignore_containers,
            overwrite=overwrite,
        )


def main():
    """Command line interface for concatenatenating list of h5 files
    """

    import argparse

    parser = argparse.ArgumentParser(
        description="Concatenates data sets of several h5 files along axis."
        " Only concatenates data sets with same name."
        " Warns if it finds group of data sets which have fewer or more data sets then"
        " files. Concatenated data sets are ordered by the file names."
    )

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        nargs="+",
        default=None,
        help="Files to concatenate (list). Must be given." " [default='%(default)s']",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Name of the output file. Must be given.",
    )
    parser.add_argument(
        "--axis",
        "-a",
        type=int,
        default=0,
        help="The axis to concatenate over. [default='%(default)s']",
    )
    parser.add_argument(
        "--overwrite",
        "-f",
        action="store_true",
        default=False,
        help="Overwrite hdf5 files if they already exist. [default=%(default)s]",
    )
    parser.add_argument(
        "--write-unpaired-dsets",
        "-w",
        action="store_true",
        default=False,
        help="Write data sets if number of dsetes do not mathch file number."
        " Else raise error. [default=%(default)s]",
    )
    args = parser.parse_args()

    if args.input is None:
        raise ValueError("You must specify concatenatenation inputs.")

    if args.output is None:
        raise ValueError("You must specify concatenatenation output file.")

    concat_dsets(
        files=args.input,
        out_file=args.output,
        axis=args.axis,
        dset_replace_patterns=None,
        ignore_containers=None,
        write_unpaired_dsets=args.write_unpaired_dsets,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
