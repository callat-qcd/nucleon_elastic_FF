# pylint: disable=C0103
"""Test for the time-slice source and t0 avarage workflow
"""
from typing import Dict
from typing import List

from itertools import product
import os

from unittest import TestCase

import h5py

from nucleon_elastic_ff.utilities import set_up_logger

TMPDIR = os.path.join(os.getcwd(), "tmp")

LOGFILE = os.path.join(os.getcwd(), "tests", "nucleon_elastic_ff_test.log")
LOGGER = set_up_logger(LOGFILE)


def setUp():
    """Creates the temp data directory
    """
    if not os.path.exists(TMPDIR):
        os.mkdir(TMPDIR)


def tearDown():
    """Creates the temp data directory
    """
    if os.path.exists(TMPDIR):
        os.rmdir(TMPDIR)


class WorkFlowTest(TestCase):
    """Tests for the time-slice source and t0 avarage workflow
    """

    file_pars: Dict[str, List[str]] = {
        "type": ["formfac_4D"],
        "ensemble": ["a09m310"],
        "stream": ["e"],
        "cfg": ["1188", "3090", "3312"],
        "flow": ["gf1.0_w3.5_n45_M51.1_L56_a1.5_mq0.00951"],
        "mom": ["px0py0pz0", "px0py0pz1"],
        "dt": ["10", "12"],
        "Nsnk": ["8"],
        "src": [],
    }

    @staticmethod
    def file_name(**kwargs) -> str:
        """Returns file name for given parameters
        """
        return (
            "{type}_{ensemble}_{stream}_{cfg}_{flow}_{mom}"
            "_dt{dt}_Nsnk{Nsnk}_{src}_SS.h5"
        ).format(**kwargs)

    def file_path(self, base, **kwargs) -> str:
        """Returns file path for given parameters
        """
        path = os.path.join(kwargs["ensemble"] + "_" + kwargs["stream"], kwargs["type"])
        return os.path.join(base, path, self.file_name(**kwargs))

    def create_random_dsets(self, **pars):
        """
        """
        dsets = {}
        return dsets

    def setUp(self):
        """Sets up directories and fake files.
        """
        self.created_files = {}
        self.created_dirs = []

        for par_values in product(*list(self.file_pars.values())):
            pars = {key: val for key, val in zip(self.file_pars.keys(), par_values)}
            file_path = self.file_path(TMPDIR, **pars)

            file_dir = os.path.dirname(file_path)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
                self.created_dirs.append(file_dir)

            dsets = self.create_random_dsets(**pars)
            with h5py.File(file_path, "w") as h5f:
                for dset_addr, dset_data in dsets.items():
                    h5f.create_dset(dset_addr, data=dset_data)
            self.created_files[file_path] = dsets

    def tearDown(self):
        """Removes fake files and directories
        """
        # for file in self.created_files:
        #     if os.path.exists(file):
        #         os.remove(file)
        #
        # for file_dir in self.created_dirs:
        #     if os.path.exists(file_dir):
        #         os.rmdir(file_dir)

    def test_01_slice(self):
        """Tests if slicing is called for the right files.
        """
        LOGGER.info("--- Running `test_01_slice` ---")
        self.assertTrue(True)
