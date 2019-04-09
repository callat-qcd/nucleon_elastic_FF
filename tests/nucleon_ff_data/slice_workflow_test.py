# pylint: disable=C0103
"""Test for the time-slice source and t0 avarage workflow
"""
from typing import Dict
from typing import List

from itertools import product
import os

from unittest import TestCase
from unittest.mock import patch
from unittest.mock import call

import h5py

from nucleon_elastic_ff.utilities import set_up_logger

from nucleon_elastic_ff.data.scripts import tslice


TMPDIR = os.path.join(os.getcwd(), "tests", "temp")

LOGFILE = "nucleon_elastic_ff_test"
LOGGER = set_up_logger(LOGFILE, mode="w")


class SliceWorkFlowTest(TestCase):
    """Tests for the time slice workflow
    """

    file_pars: Dict[str, List[str]] = {
        "type": ["formfac_4D"],
        "ensemble": ["a09m310", "a001m134"],
        "stream": ["e"],
        "cfg": ["1188", "3090", "3312"],
        "flow": ["gf1.0_w3.5_n45_M51.1_L56_a1.5_mq0.00951"],
        "mom": ["px0py0pz0", "px0py0pz1"],
        "dt": ["10", "12"],
        "Nsnk": ["2"],
        "src": ["x30y4z9t79", "x20y0z2t7"],
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

    def setUp(self):
        """Sets up directories and fake files.
        """
        if not os.path.exists(TMPDIR):
            os.mkdir(TMPDIR)
            LOGGER.info("Creating temp dir `%s`", TMPDIR)
        else:
            raise OSError("You can only run unittests if %s is empty" % TMPDIR)

        self.created_files = []
        self.created_dirs = []

        for par_values in product(*list(self.file_pars.values())):
            pars = {key: val for key, val in zip(self.file_pars.keys(), par_values)}
            file_path = self.file_path(TMPDIR, **pars)

            file_dir = os.path.dirname(file_path)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
                self.created_dirs.append(file_dir)

            LOGGER.debug("Creating fake file `%s`", file_path)
            with h5py.File(file_path, "w") as h5f:
                h5f.create_dataset("test", data=0)
            self.created_files.append(file_path)

    def tearDown(self):
        """Removes fake files and directories
        """
        for file in self.created_files:
            if os.path.exists(file):
                LOGGER.debug("Removing fake file `%s`", file)
                os.remove(file)

        for file_dir in self.created_dirs:
            if os.path.exists(file_dir):
                LOGGER.debug("Removing fake dir `%s`", file_dir)
                os.removedirs(file_dir)

        for ensemble, stream in product(
            self.file_pars["ensemble"], self.file_pars["stream"]
        ):
            tslice_path = os.path.join(
                TMPDIR, ensemble + "_" + stream, "formfac_4D_tslice"
            )
            if os.path.exists(tslice_path):
                LOGGER.debug("Removing fake dir `%s`", tslice_path)
                os.removedirs(tslice_path)

        if os.path.exists(TMPDIR):
            LOGGER.debug("Removing temp dir `%s`", TMPDIR)
            os.removedirs(TMPDIR)

    def test_01_slice(self):
        """Tests if slicing is called for the right files names.
        """
        LOGGER.info("--- Running `test_01_slice` ---")

        # Check if slice file method is called for exepected files
        with patch(
            "nucleon_elastic_ff.data.scripts.tslice.slice_file"
        ) as mocked_slice_file:
            # These are the expected calls
            mocked_calls = []
            for file_address in self.created_files:
                file_address_out = file_address.replace(
                    "formfac_4D", "formfac_4D_tslice"
                )
                overwrite = False
                mocked_calls.append(
                    call(
                        file_address,
                        file_address_out,
                        overwrite=overwrite,
                        tslice_fact=None,
                        dset_patterns=("local_current",),
                    )
                )

            tslice.tslice(TMPDIR, overwrite=False)
            try:
                mocked_slice_file.assert_has_calls(mocked_calls, any_order=True)
            except AssertionError as e:
                LOGGER.error("Failed tslice test. Mock has different calls.")
                LOGGER.error("Expected:")
                for expected_call in mocked_calls:
                    LOGGER.error("\t%s:", expected_call)
                LOGGER.error("Actual:")
                for actual_call in mocked_slice_file.call_args_list:
                    LOGGER.error("\t%s:", actual_call)
                LOGGER.exception(e)
                raise e

        # Check if folders have been created correctly
        for ensemble, stream in product(
            self.file_pars["ensemble"], self.file_pars["stream"]
        ):
            tslice_path = os.path.join(
                TMPDIR, ensemble + "_" + stream, "formfac_4D_tslice"
            )
            self.assertTrue(os.path.exists(tslice_path))
