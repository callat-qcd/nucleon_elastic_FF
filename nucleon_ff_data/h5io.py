"""Module provides h5 file interafaces.
"""
from typing import Dict
from typing import Optional
from typing import Union
from typing import List
from typing import Any

import os
import re

import numpy as np
import h5py

from nucleon_ff_data.utilities import set_up_logger

LOGGER = set_up_logger(__name__)


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
    name = os.path.join(container.filename, container.name)
    LOGGER.debug("Reading `%s`", name)

    dsets = {}
    ignore_containers = [] if ignore_containers is None else ignore_containers
    for key in container:
        obj = container[key]

        for pattern in ignore_containers:
            match = re.findall(pattern, key)
            if match:
                continue

        address = os.path.join(parent_name, key) if parent_name else key

        if isinstance(obj, h5py.Dataset):
            LOGGER.debug("Found dataset: `%s`", address)
            dsets[address] = obj[()] if load_dsets else obj
        elif isinstance(obj, h5py.Group):
            dsets.update(get_dsets(obj, parent_name=address))

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
