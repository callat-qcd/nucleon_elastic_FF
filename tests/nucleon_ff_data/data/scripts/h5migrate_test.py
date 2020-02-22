"""Tests for h5migrate
"""
import os

from unittest import TestCase

from tempfile import TemporaryDirectory

import numpy as np
import h5py

from nucleon_elastic_ff.utilities import set_up_logger

from nucleon_elastic_ff.data.h5io import get_dsets

from nucleon_elastic_ff.data.scripts.h5migrate import dset_migrate


TESTDIR = os.path.join(os.getcwd(), "tests")

LOGFILE = "nucleon_elastic_ff_test"
LOGGER = set_up_logger(LOGFILE, mode="w")


class MigrateDsetsTest(TestCase):
    """Tests different migration scenarios
    """

    _tmp_dir = None

    @property
    def tmp_address(self):
        """Returns address of temporary folder.
        """
        return self._tmp_dir.name

    def setUp(self):
        """Sets up directories and fake files.
        """
        self._tmp_dir = TemporaryDirectory(dir=TESTDIR)
        np.random.seed(42)
        LOGGER.info("Creating temp dir `%s`", self.tmp_address)

        self.dset_shapes = {"dset_1": (10, 5, 2, 1), "group1/dset_2": (10, 3, 1)}

        self.dsets = {}
        self.file_inp = os.path.join(self.tmp_address, "test_in.h5")
        with h5py.File(self.file_inp, "w") as h5f:
            for key, shape in self.dset_shapes.items():
                array = np.random.normal(size=shape)
                self.dsets[key] = array
                h5f.create_dataset(key, data=array)

    def test_01_migrate_no_overlap(self):
        """Migrates data for file with no overlap.
        """
        dsets = self.dsets.copy()
        key = "dset_3"
        dsets[key] = np.random.normal(size=(1, 2, 3))
        file_out = os.path.join(self.tmp_address, "test_out.h5")
        with h5py.File(file_out, "w") as h5f:
            h5f.create_dataset(key, data=dsets[key])

        dset_migrate(self.file_inp, file_out)

        with h5py.File(file_out, "r") as h5f:
            for key, dset in get_dsets(h5f, load_dsets=True).items():
                np.testing.assert_array_equal(dsets[key], dset)
