"""Routines for parsing information from data files and hdf addresses
"""
from typing import Union

from typing import Dict

import re

from nucleon_elastic_ff.utilities import set_up_logger

LOGGER = set_up_logger("nucleon_elastic_ff")


def parse_t_info(string: str) -> Dict[str, int]:
    r"""Extract `t0` and `tsep` info from string.

    The pattern matches e.g., ``proton_DD_dn_dn_t0_83_tsep_7_sink_mom_px0_py0_pz0``.
    Matches ``_t0_[0-9]+_tsep_[\-0-9]+_``.
    If no match is found, tries to identify ``t`` by the source location
    ``_x[0-9]+y[0-9]+z[0-9]+t[0-9]+`` and sets ``t0`` to ``t``.

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
    else:
        match = re.findall(r"x[0-9]+_y[0-9]+_z[0-9]+_t([0-9]+)", string)
        if match:
            result["t0"] = int(match[0])

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
        r"(?P<type>formfac_4D[_a-z]*|spec_4D[_a-z]*)"
        r"(?:_a(?P<ensemble>[0-9a-zA-Z]+))?"
        r"(?:_(?P<stream>[a-z]+))?"
        r"(?:_(?P<cfg>[0-9]+))?"
        r"(?:_gf(?P<gf>[0-9\.]+))?"
        r"(?:_w(?P<w>[0-9\.]+))?"
        r"(?:_n(?P<n>[0-9]+))?"
        r"(?:_M(?P<M>[0-9\.]+))?"
        r"(?:_L(?P<L>[0-9]+))?"
        r"(?:_a(?P<aa>[0-9\.]+))?"
        r"(?:_mq(?P<mq>[0-9\.]+))?"
        r"(?:_px(?P<px>[0-9]+)py(?P<py>[0-9]+)pz(?P<pz>[0-9]+))?"
        r"(?:_dt(?P<dt>[0-9]+))?"
        r"(?:_Nsnk(?P<Nsnk>[0-9]+))?"
        r"_"
        r"(?:x(?P<x>[0-9]+)+y(?P<y>[0-9]+)z(?P<z>[0-9]+)t(?P<t>[0-9]+))|(?P<avg>src_avg)"
        r"(?:_(?P<stype>[a-zA-Z]+))?"
        r".h5"
    )
    match = re.search(pattern, filename)
    if not match:
        raise ValueError("Was not able to parse file name `%s`." % filename)

    info = {}
    LOGGER.debug("Parsing info of `%s`", filename)
    for key, val in match.groupdict().items():
        LOGGER.debug("%s == %s", key, val)
        if key in ["stype", "type", "stream", "avg", "ensemble"]:
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
            info[key] = int(val) if convert_numeric and val is not None else val
        else:
            info[key] = float(val) if convert_numeric and val is not None else val

    return info
