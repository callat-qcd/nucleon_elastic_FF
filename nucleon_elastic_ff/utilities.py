"""Utility routines for nucleon_elastic_ff.data module
"""
from typing import List
from typing import Optional
from typing import Union

import logging
import re
import os


def set_up_logger(name: str) -> logging.Logger:
    """Sets up command line logger

    Loggers default level is INFO. Only contains stdout logger.

    **Arguments**
        name: str
            Name of the logger
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter("[%(asctime)s|%(name)s@%(levelname)s] %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger


def has_match(
    string: str, patterns: Union[str, List[str]], match_all: bool = False
) -> bool:
    """Returns if at least one (`match_all = False`) of the regex patterns is matched.

    **Arguments**
        string: str
            The string to check.

        patterns: List[str]
            The regex patterns to match.

        match_all: bool = False
            If true, all pattern must have a match.

    """
    match = []
    patterns = [patterns] if isinstance(patterns, str) else patterns
    for pattern in patterns:
        match.append(bool(re.findall(pattern, string)))
    return all(match) if match_all else any(match)


def find_all_files(
    root: str,
    file_patterns: Optional[List[str]] = None,
    dir_patterns: Optional[List[str]] = None,
    exclude_file_patterns: Optional[List[str]] = None,
    match_all: bool = False,
) -> List[str]:
    """Recursivly iterates directory to all files which match the patterns.

    **Arguments**
        root: str
            The string to check.

        file_patterns: Optional[List[str]] = None
            The regex patterns for files to match.

        dir_patterns: Optional[List[str]] = None
            The regex patterns for directories to match.

        exclude_file_patterns: Optional[List[str]] = None
            The regex patterns for files to not match.

        match_all: bool = False
            If true, all pattern must have a match.
    """
    all_files = []

    for file_root, _, files in os.walk(root):
        if dir_patterns is None or has_match(
            file_root, dir_patterns, match_all=match_all
        ):
            for file in files:
                file_match = file_patterns is None or has_match(
                    file, file_patterns, match_all=match_all
                )
                file_match &= exclude_file_patterns is None or not has_match(
                    file, exclude_file_patterns
                )
                if file_match:
                    all_files.append(os.path.join(file_root, file))

    return all_files
