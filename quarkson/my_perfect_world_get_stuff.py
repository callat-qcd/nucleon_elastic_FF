"""This is how my perfect world population script would work
"""
from typing import Any
from typing import Dict
from typing import List

import os

import numpy as np

from h5backend import h5File

from lattedb import DataBaseObject
from lattedb import DataDataBaseObject

META_FILE = "..."


def get_meta_info(meta_file: str) -> Dict[str, Any]:
    """Extract missing meta information from c51 file to populated database columns.

    TODO: @jason
        * Code this up
    """
    meta_infos = {}
    # populate using meta_file
    return meta_infos


def parse_path_info(path_to_file: str, path_in_file: str) -> Dict[str, Any]:
    """Read in path to hdf5 file and dataset path to extract information needed for
    populating database.

    TODO: @Jason
        * Code this up

    NOTES:
        * Parser cares about type of correlator
    """
    info = {}
    # parse path_to_file and path_in_file
    return info


def write_infos(
    path_to_file: str,
    path_in_file: str,
    data: np.ndarray,
    save_meta_db=False,
    save_data_db=False,
    save_h5=True,
    overwrite=False,
):
    """Writes information to h5file and or database if requested.

    Extracted missing meta information form `META_FILE` if wirting to database.

    Notes:
        * Does file checks

    TODO: @Andre
        * Refactor code to use this method
        * Add type of correlator tag
    """

    # @Andre: dont care about this `if`
    if save_meta_db:
        info = parse_path_info(path_to_file, path_in_file)
        meta_info = get_meta_info(META_FILE)
        info.update(meta_info)
        DataBaseObject(**info).save()

        if save_data_db:
            obj = DataBaseObject.get(**info)
            DataDataBaseObject(id=obj.id, data=data).save()

    # @Andre: care about this
    if save_h5:
        if not os.path.exists(path_to_file):
            with h5File(path_to_file, mode="w") as h5f:
                h5f.write(path_in_file, data)
        else:
            print(f"File {path_to_file} exists - skip!")


def get_info(obj_type: str) -> List[Dict[str, Any]]:
    """
    """
    meta_info = get_meta_info(META_FILE)

    if obj_type == "type_a":
        infos = get_info_type_a(**meta_info)
    elif obj_type == "type_b":
        infos = get_info_type_b(**meta_info)
    else:
        raise ValueError(f"Don't know type {obj_type}")

    return infos


def get_infos_type_a(**meta_info) -> List[Dict[str, Any]]:
    """Extracts list of information to create h5 files.

    **Arguments**
        ...

    Notes:
        * Does no file checks

    TODO: @Andre
        * Refactor existing get files to use this method.
    """
    infos = []

    for _ in ...:
        # parsing
        path_to_file = ...
        path_in_file = ...
        data = ...
        infos.append(
            {"path_to_file": path_to_file, "path_in_file": path_in_file, "data": data}
        )

    return infos


def main():
    """Writes h5files and database entries for `stuff`
    """
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(save_meta_db, type=bool, default=True)
    parser.add_argument(save_data_db, type=bool, default=False)
    parser.add_argument(save_h5, type=bool, default=True)

    args = parser.parse_args()

    for info in get_infos():
        write_infos(
            save_meta_db=args.save_meta_db,
            save_data_db=args.save_data_db,
            save_h5=args.save_h5,
            **info,
        )


if __name__ == "__main__":
    main()
