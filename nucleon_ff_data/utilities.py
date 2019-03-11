"""Utility routines for nucleon_ff_data module
"""
from typing import List
from typing import Optional

import logging
import re
import os


def set_up_logger(name: str) -> logging.Logger:
    """Sets up command line logger

    Loggers default level is WARNING. Only contains stdout logger.

    **Arguments**
        name: str
            Name of the logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    formatter = logging.Formatter("[%(asctime)s|%(name)s@%(levelname)s] %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def has_match(string: str, patterns: List[str]) -> bool:
    """Returns True if at least one of the regex patterns is matched by the file.

    **Arguments**
        string: str
            The string to check.

        patterns: List[str]
            The regex patterns to match.
    """
    match = False
    for pattern in patterns:
        match = bool(re.findall(pattern, string))
        if match:
            continue
    return match


def find_all_files(
    root: str,
    file_patterns: Optional[List[str]] = None,
    dir_patterns: Optional[List[str]] = None,
) -> List[str]:
    """Recursivly iterates directory to all files which match the patterns.

    **Arguments**
        root: str
            The string to check.

        file_patterns: Optional[List[str]] = None
            The regex patterns for files to match.

        dir_patterns: Optional[List[str]] = None
            The regex patterns for directories to match.
    """
    all_files = []
    file_patterns = [] if file_patterns is None else file_patterns
    dir_patterns = [] if dir_patterns is None else dir_patterns

    for file_root, _, files in os.walk(root):
        if has_match(file_root, dir_patterns):
            for file in files:
                if has_match(file, file_patterns):
                    all_files.append(os.path.join(file_root, file))

    return all_files
