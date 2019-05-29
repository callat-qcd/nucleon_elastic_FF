# pylint: disable=C0103
"""Test for concatinate dsets across h5 files
"""
import os

from unittest import TestCase

import numpy as np
import h5py

from nucleon_elastic_ff.utilities import set_up_logger

from nucleon_elastic_ff.data.h5io import get_dsets

from nucleon_elastic_ff.data.scripts.concat import concat_dsets


TMPDIR = os.path.join(os.getcwd(), "tests", "temp")

LOGFILE = "nucleon_elastic_ff_test"
LOGGER = set_up_logger(LOGFILE, mode="w")


class ConcatDsetsTest(TestCase):
    """Tests `nucleon_elastic_ff.data.scripts.concat.concat_dsets`
    """

    @property
    def out_file(self):
        """Returns the name of the out file
        """
        return os.path.join(TMPDIR, "conctat_out.h5")

    def setUp(self):
        """Sets up directories and fake files.
        """
        np.random.seed(42)

        if not os.path.exists(TMPDIR):
            os.mkdir(TMPDIR)
            LOGGER.info("Creating temp dir `%s`", TMPDIR)
        else:
            raise OSError("You can only run unittests if %s is empty" % TMPDIR)

        self.dset_shapes = {
            "file_a.h5": [["dset_1", (10, 5, 2, 1)], ["group1/dset_2", (10, 3, 1)]],
            "file_b.h5": [["dset_1", (13, 5, 2, 1)], ["group1/dset_3", (5, 2)]],
            "file_c.h5": [["dset_1", (7, 5, 2, 1)], ["group1/dset_2", (7, 3, 1)]],
        }

        self.dsets = {}
        for file_name, file_dsets in self.dset_shapes.items():
            file_address = os.path.join(TMPDIR, file_name)
            self.dsets[file_address] = {}
            with h5py.File(file_address, "w") as h5f:
                for dset_name, shape in file_dsets:
                    array = np.random.normal(size=shape)
                    self.dsets[file_address][dset_name] = array
                    h5f.create_dataset(dset_name, data=array)

        self.expected_dsets = {
            "dset_1": np.concatenate(
                [self.dsets[key]["dset_1"] for key in np.sort(list(self.dsets.keys()))],
                axis=0,
            )
        }

    def tearDown(self):
        """Remove temporary test dirs
        """
        for file in self.dsets:
            if os.path.exists(file):
                os.remove(file)

        if os.path.exists(self.out_file):
            os.remove(self.out_file)

        if os.path.exists(TMPDIR):
            os.removedirs(TMPDIR)

    def test_01_concat_dsets(self):
        """Tries to concat dsests
        """
        concat_dsets(
            files=list(self.dsets.keys()),
            out_file=self.out_file,
            axis=0,
            dset_replace_patterns=None,
            ignore_containers=None,
            write_unpaired_dsets=False,
            overwrite=False,
        )

        with h5py.File(self.out_file, "r") as h5f:
            actual_dsets = get_dsets(h5f, load_dsets=True)

        self.assertSequenceEqual(actual_dsets.keys(), self.expected_dsets.keys())

        for key, desired in self.expected_dsets.items():
            np.testing.assert_equal(
                actual_dsets[key],
                desired,
                err_msg="Comparison failed for dset `%s`\nactual:\n\t%s\ndesired:\n\t%s"
                % (key, actual_dsets[key], desired),
            )
