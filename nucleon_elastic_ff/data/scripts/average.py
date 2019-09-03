"""Script for time averaging correlator data
"""
from typing import List
from typing import Dict
from typing import Optional

import os
import re

import h5py

from nucleon_elastic_ff.utilities import set_up_logger
from nucleon_elastic_ff.utilities import find_all_files
from nucleon_elastic_ff.utilities import has_match

from nucleon_elastic_ff.data.h5io import get_dsets
from nucleon_elastic_ff.data.h5io import create_dset

from nucleon_elastic_ff.data.scripts.utilities import group_files
from nucleon_elastic_ff.data.scripts.utilities import parse_dset_address
from nucleon_elastic_ff.data.scripts.utilities import assert_patterns_present

LOGGER = set_up_logger("nucleon_elastic_ff")


def dset_avg(  # pylint: disable=R0914, R0913
    files: List[str],
    out_file: str,
    dset_replace_patterns: Optional[Dict[str, str]],
    overwrite: bool = False,
    expected_dsets: Optional[int] = None,
    fail_unexpected_dsets: bool = True,
):
    """Reads h5 files and exports the average of datasets across files.

    Each group in the file list will be averaged over files.

    Also the average meta info is stored in the resulting output file in the `meta`
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
            /x2y1
            /x2y2

        If you pass the ``dset_replace_patterns = {"x[0-9]y1": "x_avg_y1"}``, this will
        create the file

        .. code-block:: bash

            out.h5
            /x_avg_y1

        where the dset ``x_avg_y1`` is the average over ``file1.h5/x1y1`` and
        ``file1.h5/x2y1``. ``file1.h5/x1y2`` and ``file2.h5/x2y2`` are ignored because
        they don't match the patterns.

        **Arguments**
            files: List[str]
                List of h5 file address which will be read into memory and averaged over.

            out_file: str
                The name of the file which will contain the averages.

            dset_replace_patterns: Optional[Dict[str, str]]
                A map for how dsets in the input files are used to write to the output
                file. The routine only averages over dsets which match all keys of
                dset_replace_patterns.

            overwrite: bool = False
                Overwrite existing sliced files.

            expected_dsets: Optional[int] = None
                If specified, only writes dsets when the group contains exactly the
                specified amount of dsets.

            fail_unexpected_dsets: bool = True
                If True, fails if number of found dsets in a group is unequal to
                ``expected_dsets``.

    """
    dsets_paths = {}
    n_dsets = {}
    dset_meta = {}

    dset_replace_patterns = dset_replace_patterns or {}

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
                meta += "&".join([f"{kkey}=={vval}" for kkey, vval in meta_info.items()])

                if out_grp in dsets_paths:
                    dsets_paths[out_grp].append((file, key))
                    n_dsets[out_grp] += 1
                    dset_meta[out_grp] += "\n" + meta
                else:
                    dsets_paths[out_grp] = [(file, key)]
                    n_dsets[out_grp] = 1
                    dset_meta[out_grp] = meta

    if expected_dsets is not None and fail_unexpected_dsets:
        for group, count in n_dsets.items():
            if count != expected_dsets:
                raise KeyError(
                    (
                        "Expected %d dests but found %d dsets for group %s"
                        "\nMeta info:\n\t%s"
                    )
                    % (len(files), count, group, dset_meta[group])
                )

    LOGGER.info("Writing `%d` dsets to `%s`", len(dsets_paths), out_file)
    with h5py.File(out_file) as h5f:
        for key, paths in dsets_paths.items():
            LOGGER.debug(
                "Writing dset `%s` (average of %d dsets) with meta info:\n\t`%s`",
                key,
                n_dsets[key],
                dset_meta[key],
            )

            if expected_dsets is not None and n_dsets[key] != expected_dsets:
                LOGGER.debug("Skipping dset because not right amount of entries")
                continue

            acc = 0
            for file, path in paths:
                with h5py.File(file, "r") as h5fin:
                    acc += h5fin[path][()]

            create_dset(h5f, key, acc / n_dsets[key], overwrite=overwrite)
            h5f[key].attrs["meta"] = dset_meta[key]


def source_average(  # pylint: disable=R0913, R0914
    root: str,
    overwrite: bool = False,
    n_expected_sources: Optional[int] = None,
    expected_sources: Optional[List[str]] = None,
    file_name_addition: Optional[str] = None,
    additional_file_patterns: Optional[List[str]] = None,
):
    """Recursively scans directory for files and averages matches which over specified
    component.

    The input files must be h5 files (ending with ".h5") and must have
    `formfac_4D_tslice`in their file name.
    Files which have `formfac_4D_tslice_src_avg` as name are excluded.
    Also, this routine ignores exporting to files which already exist.

    **Arguments**
        root: str
            The directory to look for files.

        overwrite: bool = False
            Overwrite existing sliced files.

        n_expected_sources: Optional[int] = None
            Added control to pass excepted number of sources.
            If given and sources in one group is less than a certain number, raises
            ValueError.

        expected_sources: Optional[List[str]] = None
            Adds expected sources to file filter patterns.
            After files have been filtered and grouped, checks if all strings in this
            list are present in the file group.
            Note: this counts the number of files not the number of dsets within a file.
            This also overwrites ``n_expected_sources``.
            If not exactly all sources are found in the group, raises AssertionError.

        file_name_addition: Optional[str] = None
            Appends this string to the file name if not None.

        additional_file_patterns: Optional[List[str]] = None
            Only consideres files for averaging if additional patterns are fulfilled.
    """
    LOGGER.info("Running source average")

    avg_over_file_keys = ("x", "y", "z", "t")
    file_replace_pattern = {
        "x[0-9]+y[0-9]+z[0-9]+t[0-9]+": "src_avg"
        + (file_name_addition if file_name_addition is not None else ""),
        "formfac_4D_tslice": "formfac_4D_tslice_src_avg",
    }
    dset_replace_pattern = {
        r"x(?P<x>[0-9]+)_y(?P<y>[0-9]+)_z(?P<z>[0-9]+)_t(?P<t>[0-9]+)": "src_avg",
        r"t0_(?P<t0>[0-9]+)_": "",
    }

    file_patterns = [r".*\.h5$", "formfac_4D_tslice"]
    file_patterns += list(file_replace_pattern.keys())
    if additional_file_patterns is not None:
        file_patterns += additional_file_patterns.split()
    LOGGER.info("File patterns %s", file_patterns)

    files = find_all_files(
        root,
        file_patterns=file_patterns,
        exclude_file_patterns=list(file_replace_pattern.values()),
        match_all=True,
    )
    if expected_sources is not None:
        files = [file for file in files if has_match(file, expected_sources)]

    n_expected_sources = (
        len(expected_sources) if expected_sources else n_expected_sources
    )

    file_groups = group_files(files, keys=avg_over_file_keys)

    for file_group in file_groups.values():
        out_file = file_group[0]

        if n_expected_sources:
            if len(file_group) != n_expected_sources:
                raise AssertionError(
                    "Expected %d sources in one average group but only received %d"
                    % (n_expected_sources, len(file_group))
                )

        if expected_sources:
            assert_patterns_present(expected_sources, file_group)

        for pat, subs in file_replace_pattern.items():
            out_file = re.sub(pat, subs, out_file)

        base_dir = os.path.dirname(out_file)
        if not os.path.exists(base_dir):
            LOGGER.info("Creating `%s`", base_dir)
            os.makedirs(base_dir)

        dset_avg(
            file_group,
            out_file,
            dset_replace_pattern,
            overwrite=overwrite,
            expected_dsets=None,
        )


def spec_average(  # pylint: disable=R0913, R0914
    root: str,
    overwrite: bool = False,
    n_expected_sources: Optional[int] = None,
    expected_sources: Optional[List[str]] = None,
    file_name_addition: Optional[str] = None,
):
    """Recursively scans directory for files and averages matches which over specified
    component.

    Averages over source, spin and parity without shifting or slicing. Thus, the data
    must already be in the correct shape.

    The input files must be h5 files (ending with ".h5") and must have `spec_4D_tslice`
    in their file name. Files which have `spec_4D_tslice_avg` as name are excluded.
    Also, this routine ignores exporting to files which already exist.

    **Arguments**
        root: str
            The directory to look for files.

        overwrite: bool = False
            Overwrite existing sliced files.

        n_expected_sources: Optional[int] = None
            Added control to pass excepted number of sources.
            If given and sources in one group is less than a certain number, raises
            AssertionError.

        expected_sources: Optional[List[str]] = None
            Adds expected sources to file filter patterns.
            After files have been filtered and grouped, checks if all strings in this
            list are present in the file group.
            Note: this counts the number of files not the number of dsets within a file.
            This also overwrites ``n_expected_sources``.
            If not exactly all sources are found in the group, raises AssertionError.

        file_name_addition: Optional[str] = None
            Appends this string to the file name if not None.
    """
    LOGGER.info("Running source average")

    avg_over_file_keys = ("x", "y", "z", "t")
    file_replace_pattern = {
        "x[0-9]+y[0-9]+z[0-9]+t[0-9]+": "src_avg"
        + (file_name_addition if file_name_addition is not None else ""),
        "spec_4D_tslice": "spec_4D_tslice_avg",
        # "spec_4D": "spec_4D_avg",
    }
    dset_replace_pattern = {
        r"x(?P<x>[0-9]+)_y(?P<y>[0-9]+)_z(?P<z>[0-9]+)_t(?P<t>[0-9]+)": "src_avg",
        r"spin_(?:up|dn)": "spin_avg",
    }

    file_patterns = [r".*\.h5$", "spec_4D_tslice"]
    file_patterns += list(file_replace_pattern.keys())

    files = find_all_files(
        root,
        file_patterns=file_patterns,
        exclude_file_patterns=list(file_replace_pattern.values()),
        match_all=True,
    )
    if expected_sources is not None:
        files = [file for file in files if has_match(file, expected_sources)]

    n_expected_sources = (
        len(expected_sources) if expected_sources else n_expected_sources
    )

    file_groups = group_files(files, keys=avg_over_file_keys)

    for file_group in file_groups.values():
        out_file = file_group[0]

        if n_expected_sources:
            if len(file_group) != n_expected_sources:
                raise AssertionError(
                    "Expected %d sources in one average group but only received %d"
                    % (n_expected_sources, len(file_group))
                )

        if expected_sources:
            assert_patterns_present(expected_sources, file_group)

        for pat, subs in file_replace_pattern.items():
            out_file = re.sub(pat, subs, out_file)

        base_dir = os.path.dirname(out_file)
        if not os.path.exists(base_dir):
            LOGGER.info("Creating `%s`", base_dir)
            os.makedirs(base_dir)

        dset_avg(
            file_group,
            out_file,
            dset_replace_pattern,
            overwrite=overwrite,
            expected_dsets=None,
        )


def main():
    """Command line interface for averaging list of h5 files
    """

    import argparse

    parser = argparse.ArgumentParser(
        description="Reads h5 files and exports the average of datasets across files."
        " Each group in the file list will be averaged over files."
        " Only writes dsets if number matches the number specified files for each group"
        " (see `--pass-expected-dsets` flag in case you want it to fail)."
    )

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        nargs="+",
        default=None,
        help="Files to average (list). Must be given.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Name of the output file. Must be given.",
    )
    parser.add_argument(
        "--overwrite",
        "-f",
        action="store_true",
        default=False,
        help="Overwrite hdf5 files if they already exist. [default=%(default)s]",
    )
    parser.add_argument(
        "--fail-unexpected-dsets",
        "-u",
        action="store_true",
        default=False,
        help="If False, does not raises exception if number of found dsets"
        " are unequal to the number of input files (just skips them)."
        " [default=%(default)s]",
    )
    args = parser.parse_args()

    if args.input is None:
        raise ValueError("You must specify concatenatenation inputs.")

    if args.output is None:
        raise ValueError("You must specify concatenatenation output file.")

    dset_avg(  # pylint: disable=R0914
        files=args.input,
        out_file=args.output,
        dset_replace_patterns=None,
        overwrite=args.overwrite,
        expected_dsets=len(args.input),
        fail_unexpected_dsets=args.fail_unexpected_dsets,
    )


if __name__ == "__main__":
    main()
