"""Routines for parsing information from data files and hdf addresses
"""
from typing import Union

from typing import Dict

import re

from nucleon_elastic_ff.utilities import set_up_logger

LOGGER = set_up_logger("nucleon_elastic_ff")


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
        for key, val in match.groupdict().items():
            result[key] = int(val)

    return result


def parse_file_info(
    filename: str, convert_numeric: bool = True
) -> Dict[str, Union[int, float, str]]:
    """Parses the filename and returns dict corresponding to file parameters.

    **Arguments**
        filename: str
            File that starts with `formfac_4D_<...>.h5` where the elipses are not
            optional.

        convert_numeric: bool = True
            Converts float & int strings to floats & ints.
            If false, leave them as a string.

    **Raises**
        ValueError
            If one key is not specified.
    """
    pattern = (
        r"(?P<type>formfac_4D[_a-z]*)"
        "_"
        r"a(?P<ensemble>[0-9a-zA-Z]+)"
        r"_"
        r"(?P<stream>[a-z]+)"
        r"_"
        r"(?P<cfg>[0-9]+)"
        r"_"
        r"gf(?P<gf>[0-9\.]+)"
        r"_"
        r"w(?P<w>[0-9\.]+)"
        r"_"
        r"n(?P<n>[0-9]+)"
        r"_"
        r"M(?P<M>[0-9\.]+)"
        r"_"
        r"L(?P<L>[0-9]+)"
        r"_"
        r"a(?P<aa>[0-9\.]+)"
        r"_"
        r"mq(?P<mq>[0-9\.]+)"
        r"_"
        r"px(?P<px>[0-9]+)py(?P<py>[0-9]+)pz(?P<pz>[0-9]+)"
        r"_"
        r"dt(?P<dt>[0-9]+)"
        r"_"
        r"Nsnk(?P<Nsnk>[0-9]+)"
        r"_"
        r"(?:x(?P<x>[0-9]+)+y(?P<y>[0-9]+)z(?P<z>[0-9]+)t(?P<t>[0-9]+))|(?P<avg>src_avg)"
        r"_"
        r"(?P<stype>[a-zA-Z]+)"
        r".h5"
    )
    match = re.search(pattern, filename)
    if not match:
        raise ValueError("Was not able to parse file name `%s`." % filename)

    info = {}
    LOGGER.debug("Parsing info of `%s`", filename)
    for key, val in match.groupdict().items():
        LOGGER.debug("%s == %s", key, val)
        if key in ["stype", "type", "stream", "avg"]:
            info[key] = val
        elif key in [
            "cfg",
            "n",
            "L",
            "px",
            "py",
            "pz",
            "dt",
            "Nsnk",
            "x",
            "y",
            "z",
            "t",
        ]:
            info[key] = int(val) if convert_numeric else val
        else:
            info[key] = float(val) if convert_numeric else val

    if convert_numeric:
        info["a"] /= 1000

    return info
