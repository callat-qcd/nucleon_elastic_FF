"""More specialised utility scripts which help grouping similar files.
"""
from typing import List
from typing import Union
from typing import Dict
from typing import Tuple
from typing import Optional

import re

from nucleon_elastic_ff.utilities import set_up_logger
from nucleon_elastic_ff.utilities import has_match

from nucleon_elastic_ff.data.parsing import parse_file_info

LOGGER = set_up_logger("nucleon_elastic_ff")


def group_files(
    all_files: List[str], keys: List[str]
) -> Dict[Dict[str, Union[int, float, str]], str]:
    """Collects files by properties which are not allowed to differ.

    Parses the information from file names and groups them according to similar
    parameters and uses `nucleon_elastic_ff.data.parsing.parse_file_info` under the hood.
    Labes in `keys` are allowed to differ and must match the output of `parse_file_info`.

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
    address: str, dset_replace_patterns: Optional[Dict[str, str]] = None
) -> Tuple[str, Dict[str, str]]:
    """Adjust address of file with substitutions and extract substitution information

    **Arguments**
        address: str
            The address to process.

        dset_replace_patterns: Optional[Dict[str, str]] = None
            Map for replacements. Must have regex capture groups, e.g., "(?P<x>[0-9]+)"
            to extract meta info.

    **Returns**
        The address after substitututions and a dictionary for parsed meta information.
    """
    dset_replace_patterns = dset_replace_patterns or {}
    out_grp = address
    meta_info = {}
    for pat, subs in dset_replace_patterns.items():
        out_grp = re.sub(pat, subs, out_grp)

        match = re.search(pat, address)
        if match:
            meta_info.update(match.groupdict())

    return out_grp, meta_info


def assert_patterns_present(expected_patterns: List[str], file_group: List[str]):
    """Checks if all ``expected_patterns`` can be found in ``file_group``.

    Iterates over all files of ``file_group`` and checks if the strings in
    ``expected_patterns`` have matches in the file name.

    **Arguments**
        expected_patterns: List[str]
            List of regex expression.

        file_group: List[str]
            List of file names to check.

    **Raises**
        AssertionError: If not all expected sources are present or a expected source is
        present more then once.
    """
    present_patterns = set()
    for file in file_group:
        for expected_pattern in expected_patterns:
            if has_match(file, expected_pattern):
                if not expected_pattern in present_patterns:
                    present_patterns.add(expected_pattern)
                    break
                else:
                    raise AssertionError(
                        "Found expected source `%s` twice in file group\n\t"
                        % expected_pattern
                        + "Expected sources\n\t"
                        + "\n\t".join(file_group)
                    )

    if present_patterns != set(expected_patterns):
        raise AssertionError(
            "Did not find all expected sources in in file group\n"
            "Expected sources which are missing:\n\t"
            + "\n\t".join(set(expected_patterns).difference(present_patterns))
            + "\nFile group:\n\t"
            + "\n\t".join(file_group)
        )
