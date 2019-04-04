"""Compares routines against results used for export.

Must be run on summit.
"""
import os

from unittest import TestCase
from unittest import skipIf

from nucleon_elastic_ff.utilities import set_up_logger

from nucleon_elastic_ff.data.h5io import assert_h5files_equal

from nucleon_elastic_ff.data.scripts import tslice
from nucleon_elastic_ff.data.scripts import average


TMPDIR = os.path.join(os.getcwd(), "tests", "temp")

LOGFILE = "nucleon_elastic_ff_test"
LOGGER = set_up_logger(LOGFILE, mode="w")

DATAROOT = "/ccs/home/ckoerber/data/"

SRCFILEROOT = (
    "formfac_4D_a09m310_e_1140"
    "_gf1.0_w3.5_n45_M51.1_L56_a1.5_mq0.00951_px0py0pz0_dt10_Nsnk8"
)
SRCS = [
    "x12y13z15t35",
    "x28y29z31t35",
    "x13y26z3t59",
    "x29y10z19t59",
    "x19y4z26t11",
    "x3y20z10t11",
    "x21y10z29t83",
    "x5y26z13t83",
]
SRCFILES = [f"{SRCFILEROOT}_{src}_SS.h5" for src in SRCS]


class LegacyTest(TestCase):
    """Compares routines against legacy files produce by @walkloud and @ckoerber.
    """

    cfg = "1140"

    def setUp(self):
        """Sets up directories and fake files.
        """
        if not os.path.exists(TMPDIR):
            os.mkdir(TMPDIR)
            LOGGER.info("Creating temp dir `%s`", TMPDIR)
        else:
            raise OSError("You can only run unittests if %s is empty" % TMPDIR)

        for formfac_4D in SRCFILES:
            path = os.path.join("formfac_4D", self.cfg, formfac_4D)
            os.link(os.path.join(DATAROOT, path), os.path.join(TMPDIR, path))

    def tearDown(self):
        """Removes fake files and directories
        """
        for formfac_4D in SRCFILES:
            path = os.path.join(TMPDIR, "formfac_4D", self.cfg, formfac_4D)
            if os.path.exists(path):
                LOGGER.debug("Removing test formfac_4D dir `%s`", path)
                os.removedirs(path)

        if os.path.exists(TMPDIR):
            LOGGER.debug("Removing temp dir `%s`", TMPDIR)
            os.removedirs(TMPDIR)

    @skipIf(
        not os.path.exists(DATAROOT),
        "Could not locate dir %s. This test must be run on summit." % DATAROOT,
    )
    def test_01_walkloud_vs_ckoerber(self):
        """Compares walklouds legacy file against ckoerbers file
        """
        walkloud = os.listdir(
            DATAROOT, "formfac_4D_tslice_src_avg", self.cfg, "awl_avg.h5"
        )
        ckoerber = os.listdir(
            DATAROOT,
            "formfac_4D_tslice",
            self.cfg,
            "formfac_4D_tslice_src_avg_a09m310_e_1140"
            "_gf1.0_w3.5_n45_M51.1_L56_a1.5_mq0.00951"
            "_px0py0pz0_dt10_Nsnk8_src_avg_SS.h5",
        )
        assert_h5files_equal(walkloud, ckoerber, atol=0, rtol=1.0e-8)

    @skipIf(
        not os.path.exists(DATAROOT),
        "Could not locate dir %s. This test must be run on summit." % DATAROOT,
    )
    def test_slice_average(self):
        """Slices files
        """
        with self.subTest("Slicing"):
            tslice.tslice(TMPDIR, overwrite=False)

            created_files = sorted(os.listdir(TMPDIR, "formfac_4D_tslice", self.cfg))
            expected_files = sorted(os.listdir(DATAROOT, "formfac_4D_tslice", self.cfg))

            self.assertEqual(len(created_files), len(expected_files))

            for expected_file, actual_file in zip(expected_files, created_files):
                assert_h5files_equal(expected_file, actual_file, atol=0, rtol=1.0e-8)

        with self.subTest("Averaging"):
            average.source_average(TMPDIR, overwrite=False, n_expected_sources=8)

            created_files = sorted(
                os.listdir(TMPDIR, "formfac_4D_tslice_src_avg", self.cfg)
            )
            expected_files = sorted(
                os.listdir(DATAROOT, "formfac_4D_tslice_src_avg", self.cfg)
            )

            self.assertEqual(len(created_files), len(expected_files))

            for expected_file, actual_file in zip(expected_files, created_files):
                assert_h5files_equal(expected_file, actual_file, atol=0, rtol=1.0e-8)
