"""Module provides h5 file interafaces.
"""
from typing import Dict
from typing import Optional
from typing import Union
from typing import List
from typing import Any

import os

import numpy as np
import h5py

from nucleon_elastic_ff.utilities import set_up_logger
from nucleon_elastic_ff.utilities import has_match

LOGGER = set_up_logger("nucleon_elastic_ff")


def get_dsets(
    container: Union[h5py.File, h5py.Group],
    parent_name: Optional[str] = None,
    load_dsets: bool = False,
    ignore_containers: Optional[List[str]] = None,
) -> Dict[str, Union[h5py.Dataset, np.ndarray]]:
    """Access an HDF5 container and extracts datasets.

    The method is iteratively called if the container contains further containers.

    **Arguments**
        container: Union[h5py.File, h5py.Group]
            The HDF5 group or file to iteratetively search.

        parent_name: Optional[str] = None
            The name of the parent container.

        load_dsets: bool = False
            If False, data sets are not opened (lazy load).
            If True, returns Dict with numpy arrays as values.

        ignore_containers: Optional[List[str]] = None
            A list of HDF5 containers to ignore when iteratively solving.
            Can be regex expressions.

    **Returns**
        datasets: Dict[str, Union[h5py.Dataset, np.ndarray]]
            A dictionary containing the full path HDF path (e.g., `groupA/subgroupB`)
            to the data set as keys and the unloaded values of the set as values.
    """
    if isinstance(container, h5py.File):
        LOGGER.info("Locating all dsets of h5 file `%s`", container.filename)

    dsets = {}
    ignore_containers = [] if ignore_containers is None else ignore_containers
    for key in container:
        obj = container[key]

        if has_match(key, ignore_containers):
            continue

        address = os.path.join(parent_name, key) if parent_name else key

        if isinstance(obj, h5py.Dataset):
            LOGGER.debug("\t`%s`", address)
            dsets[address] = obj[()] if load_dsets else obj
        elif isinstance(obj, h5py.Group):
            dsets.update(get_dsets(obj, parent_name=address, load_dsets=load_dsets))

    return dsets


def create_dset(h5f: h5py.File, key: str, data: Any, overwrite: bool = False):
    """Creates or overwrites (if requested) dataset in HDF5 file.

    **Arguments**
        h5f: h5py.File
            The file to write to.

        key: str
            The name of the dataset.

        data: Any
            The data for the dataset.

        overwrite: bool = False
            Wether data shall be overwritten.
    """
    LOGGER.debug("Writing dataset:`%s`", key)
    if key in h5f:
        if overwrite:
            del h5f[key]
            h5f.create_dataset(key, data=data)
        else:
            LOGGER.info("Skipping dataset because exists:`%s`", key)
    else:
        h5f.create_dataset(key, data=data)


def assert_h5files_equal(  # pylint: disable=R0913
    actual: str,
    expected: str,
    atol: float = 1.0e-7,
    rtol: float = 1.0e-7,
    group_actual: Optional[str] = None,
    group_expected: Optional[str] = None,
):
    """Reads to HDF5 files, compares if they have equal datasets.

    **Arguments**
        actual: str
            File name for actual input data.

        expected: str
            File name for expected input data.

        atol: float = 1.0e-7
            Absolute error tolarance. See numpy `assert_allcolse`.

        rtol: float = 1.0e-7
            Relative error tolarance. See numpy `assert_allcolse`.

    **Raises**
        AssertionError:
            If datasets are different (e.g., not present or actual data is different.)
    """
    with h5py.File(actual, "r") as h5f_a:
        dsets_a = (
            get_dsets(h5f_a, load_dsets=False)
            if group_actual is None
            else {group_actual: h5f_a[group_actual]}
        )

        with h5py.File(expected, "r") as h5f_e:
            dsets_e = (
                get_dsets(h5f_e, load_dsets=False)
                if group_expected is None
                else {group_expected: h5f_e[group_expected]}
            )

            actual_keys = set(dsets_a.keys())
            expected_keys = set(dsets_e.keys())

            if actual_keys != expected_keys:
                raise AssertionError(
                    (
                        "Files have different datasets:"
                        "\n---Dsets in actual but not in expected---\n\t%s"
                        "\n---Dsets in expected but not in actual---\n\t%s"
                    )
                    % (
                        "\n\t".join(actual_keys.difference(expected_keys)),
                        "\n\t".join(expected_keys.difference(actual_keys)),
                    )
                )

            for key in actual_keys:
                np.testing.assert_allclose(
                    dsets_a[key],
                    dsets_e[key],
                    atol=atol,
                    rtol=rtol,
                    err_msg="Dataset `%s` has unequal values." % key,
                )
