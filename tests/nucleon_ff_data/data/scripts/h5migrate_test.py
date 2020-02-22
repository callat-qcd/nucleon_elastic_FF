"""Tests for h5migrate
"""
import os

from unittest import TestCase
from unittest.mock import patch

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

    def test_02_migrate_overlap_equal(self):
        """Migrates data for file with overlap but files agree.
        """
        dsets = self.dsets.copy()
        key = "dset_3"
        dsets[key] = np.random.normal(size=(1, 2, 3))
        file_out = os.path.join(self.tmp_address, "test_out.h5")
        with h5py.File(file_out, "w") as h5f:
            h5f.create_dataset(key, data=dsets[key])
            h5f.create_dataset("dset_1", data=dsets["dset_1"])

        dset_migrate(self.file_inp, file_out)

        with h5py.File(file_out, "r") as h5f:
            for key, dset in get_dsets(h5f, load_dsets=True).items():
                np.testing.assert_array_equal(dsets[key], dset)

    @patch("logging.Logger.warning")
    def test_03_migrate_overlap_not_equal(self, mock):
        """Migrates data for file with overlap and files dont agree.
        """
        dsets = self.dsets.copy()
        key = "dset_3"
        dsets[key] = np.random.normal(size=(1, 2, 3))
        file_out = os.path.join(self.tmp_address, "test_out.h5")
        with h5py.File(file_out, "w") as h5f:
            h5f.create_dataset(key, data=dsets[key])
            h5f.create_dataset("dset_1", data=dsets["dset_1"] + 1)

        atol = 0.0
        rtol = 1.0e-7

        dset_migrate(self.file_inp, file_out, atol=atol, rtol=rtol)

        with h5py.File(file_out, "r") as h5f:
            for key, dset in get_dsets(h5f, load_dsets=True).items():
                if key != "dset_1":
                    np.testing.assert_array_equal(dsets[key], dset)
                else:
                    self.assertFalse(np.allclose(dsets[key], dset))

        mock.assert_called_with(
            "Dset `%s` in input file `%s` does not aggree with file `%s`"
            " for atol=%g and rtol=%g",
            "dset_1",
            self.file_inp,
            file_out,
            atol,
            rtol,
        )

    def test_04_migrate_nan_data(self):
        """Migrates data for file with nan data.
        """
        bad_key = "bad_key"
        bad_array = np.random.uniform(size=(3, 3, 3))
        bad_array[0, 0, 0] = np.NaN
        with h5py.File(self.file_inp, "w") as h5f:
            h5f.create_dataset(bad_key, data=bad_array)

        dsets = self.dsets.copy()
        key = "dset_3"
        dsets[key] = np.random.normal(size=(1, 2, 3))
        file_out = os.path.join(self.tmp_address, "test_out.h5")
        with h5py.File(file_out, "w") as h5f:
            h5f.create_dataset(key, data=dsets[key])

        with self.assertRaises(ValueError):
            dset_migrate(self.file_inp, file_out)
