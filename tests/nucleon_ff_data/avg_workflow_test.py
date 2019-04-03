# pylint: disable=C0103
"""Test for the time-slice source and t0 avarage workflow
"""
from typing import Dict
from typing import List

from itertools import product
import os

from unittest import TestCase
from unittest.mock import patch

import h5py

from nucleon_elastic_ff.utilities import set_up_logger

from nucleon_elastic_ff.data.scripts import average


TMPDIR = os.path.join(os.getcwd(), "tests", "temp")

LOGFILE = "nucleon_elastic_ff_test"
LOGGER = set_up_logger(LOGFILE, mode="w")


class AvgWorkFlowTest(TestCase):
    """Tests for the avg workflow
    """

    file_pars: Dict[str, List[str]] = {
        "type": ["formfac_4D_tslice"],
        "ensemble": ["a09m310", "a001m134"],
        "stream": ["e"],
        "cfg": ["1188", "3090", "3312"],
        "flow": ["gf1.0_w3.5_n45_M51.1_L56_a1.5_mq0.00951"],
        "mom": ["px0py0pz0", "px0py0pz1"],
        "dt": ["10", "12"],
        "Nsnk": ["2"],
        "src": {"x20y0z2t7", "x30y4z9t79"},
    }

    dset_pars: Dict[str, List[str]] = {
        "current": [f"A{n+1}" for n in range(4)]
        + [f"V{n+1}" for n in range(4)]
        + ["S", "P"],
        "parity": ["", "np"],
        "iso": ["UU", "DD"],
        "spin": ["up_up", "dn_dn"],
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

    def out_file(self, base, **kwargs) -> str:
        """Returns name of the average file for given input pars
        """
        pars = kwargs.copy()
        pars["src"] = "src_avg"
        pars["type"] = "formfac_4D_tslice_src_avg"
        path = os.path.join(pars["ensemble"] + "_" + pars["stream"], pars["type"])
        return os.path.join(base, path, self.file_name(**pars))

    @staticmethod
    def dset_path(file_pars: Dict[str, str], group_pars: Dict[str, str]) -> str:
        """Returns data set path path for given parameters
        """
        all_pars = {**file_pars, **group_pars}
        return os.path.join(
            (
                "proton_"
                + (group_pars["parity"] + "_" if group_pars["parity"] else "")
                + "{iso}_{spin}_sink_mom_{mom}"
            ).format(**all_pars),
            group_pars["current"],
            file_pars["src"],
            "4D_correlator",
            "local_current",
        )

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
        self.file_groups = {}

        for par_values in product(*list(self.file_pars.values())):
            file_pars = {key: val for key, val in zip(self.file_pars.keys(), par_values)}
            file_path = self.file_path(TMPDIR, **file_pars)

            file_dir = os.path.dirname(file_path)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
                self.created_dirs.append(file_dir)

            LOGGER.debug("Creating fake file `%s`", file_path)
            with h5py.File(file_path, "w") as h5f:
                for dset_values in product(*list(self.dset_pars.values())):
                    dset_pars = {
                        key: val for key, val in zip(self.dset_pars.keys(), dset_values)
                    }
                    h5f.create_dataset(self.dset_path(file_pars, dset_pars), data=0)
            self.created_files.append(file_path)

            out_file = self.out_file(TMPDIR, **file_pars)
            if out_file in self.file_groups:
                self.file_groups[out_file].append(file_path)
            else:
                self.file_groups[out_file] = [file_path]

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
            avg_path = os.path.join(
                TMPDIR, ensemble + "_" + stream, "formfac_4D_tslice_src_avg"
            )
            if os.path.exists(avg_path):
                LOGGER.debug("Removing fake dir `%s`", avg_path)
                os.removedirs(avg_path)

        if os.path.exists(TMPDIR):
            LOGGER.debug("Removing temp dir `%s`", TMPDIR)
            os.removedirs(TMPDIR)

    def test_01_avg_raise_expected_source_exception(self):
        """Tests if avaraging fails if the number of sources is incorrect
        """
        LOGGER.info("--- Running `test_01_avg_raise_expected_source_exception` ---")
        with self.assertRaises(ValueError):
            average.source_average(TMPDIR, overwrite=False, n_expected_sources=3)

    def test_02_dset_avg_call_args(self):  # pylint: disable=R0914
        """Tests if the underlaying method `dset_avg` is called with the correct args.
        """
        LOGGER.info("--- Running `test_01_dset_avg_call_args` ---")

        dset_replace_pattern = {
            r"x(?P<x>[0-9]+)_y(?P<y>[0-9]+)_z(?P<z>[0-9]+)_t(?P<t>[0-9]+)": "src_avg",
            r"t0_(?P<t0>[0-9]+)_": "",
        }

        # Check if avg file method is called for exepected files
        with patch(
            "nucleon_elastic_ff.data.scripts.average.dset_avg"
        ) as mocked_dset_avg:
            # These are the expected calls
            mocked_calls = []
            for out_file, file_group in self.file_groups.items():
                mocked_calls.append((file_group, out_file, dset_replace_pattern))

            average.source_average(TMPDIR, overwrite=False, n_expected_sources=2)

            self.assertEqual(len(mocked_dset_avg.call_args_list), len(mocked_calls))

            for mocked_call in mocked_calls:
                has_match = False
                expected_fg, expected_of, expected_drp = mocked_call
                for actual_call in mocked_dset_avg.call_args_list:
                    actual_fg, actual_of, actual_drp = actual_call[0]
                    has_match = (
                        set(expected_fg) == set(actual_fg)
                        and expected_of == actual_of
                        and expected_drp == actual_drp
                    )
                    if has_match:
                        break

                if not has_match:
                    e = AssertionError(
                        "Failed source_average test."
                        " Mock has different calls."
                        " View `%s.log` for more details.",
                        LOGFILE,
                    )
                    LOGGER.debug("Expected:")
                    LOGGER.debug("\t%s:", mocked_call)
                    LOGGER.debug("Actual:")
                    for actual_call in mocked_dset_avg.call_args_list:
                        LOGGER.debug("\t%s:", actual_call)
                    raise e

        # Check if folders have been created correctly
        for ensemble, stream in product(
            self.file_pars["ensemble"], self.file_pars["stream"]
        ):
            tslice_path = os.path.join(
                TMPDIR, ensemble + "_" + stream, "formfac_4D_tslice_src_avg"
            )
            self.assertTrue(os.path.exists(tslice_path))
