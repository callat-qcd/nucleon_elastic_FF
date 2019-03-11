"""Routines for parsing information from data files and hdf addresses
"""
from typing import Dict

import re


def parse_t_info(string: str) -> Dict[str, int]:
    """Extract `t0` and `tsep` info from string.

    The pattern matches e.g., `proton_DD_dn_dn_t0_83_tsep_7_sink_mom_px0_py0_pz0`

    **Arguments**
        string: str
            The string to match


    **Returns**
        Dict[str, int]:
            Dictionary with keys for `t0` and `tsep`
    """
    result = {}

    match = re.search(r"_t0_(?P<t0>[0-9]+)_tsep_(?P<tsep>[\-0-9]+)_", string)
    if match:
        for key in result:
            result[key] = int(match.group(key))

    return result
