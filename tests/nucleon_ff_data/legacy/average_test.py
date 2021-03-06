"""Compares tsliced routines against results used for export.
"""
from os.path import join

from unittest import TestCase

from nucleon_elastic_ff.test_utilities import CommandTest
from nucleon_elastic_ff.test_utilities import LOGGER

from nucleon_elastic_ff.data.scripts.average import source_average
from nucleon_elastic_ff.data.scripts.average import spec_average


class FormfacAverageTest(CommandTest, TestCase):
    """Runs average on legacy ``formfac_4D`` files and compares results"""

    link_files = [
        join("formfac_4D_tslice", "formfac_4D_tslice_px0py0pz0_Nsnk1_x0y1z2t2.h5"),
        join("formfac_4D_tslice", "formfac_4D_tslice_px0py0pz0_Nsnk1_x3y1z2t4.h5"),
    ]
    check_files = [
        join(
            "formfac_4D_tslice_src_avg",
            "formfac_4D_tslice_src_avg_px0py0pz0_Nsnk1_src_avg.h5",
        )
    ]

    def command(self):
        """Command which will be executed by the unittest.
        """
        LOGGER.info("Running `average`")
        source_average(
            join(self.tmp_address, "formfac_4D_tslice"),
            overwrite=False,
            n_expected_sources=2,
        )


class FormfacAverageTestExpectedSources(CommandTest, TestCase):
    """Runs average on ``formfac_4D`` files with specified sources and compares results
    """

    link_files = [
        join("formfac_4D_tslice", "formfac_4D_tslice_px0py0pz0_Nsnk1_x0y1z2t2.h5"),
        join("formfac_4D_tslice", "formfac_4D_tslice_px0py0pz0_Nsnk1_x3y1z2t4.h5"),
    ]
    check_files = [
        join(
            "formfac_4D_tslice_src_avg",
            "formfac_4D_tslice_src_avg_px0py0pz0_Nsnk1_src_avg.h5",
        )
    ]

    def command(self):
        """Command which will be executed by the unittest.
        """
        LOGGER.info("Running `average`")
        source_average(
            join(self.tmp_address, "formfac_4D_tslice"),
            overwrite=False,
            expected_sources=["x0y1z2t2", "x3y1z2t4"],
        )


class FormfacAverageTestOneExpectedSource(CommandTest, TestCase):
    """Runs average on ``formfac_4D`` files with one specified source and compares res.
    """

    link_files = [
        join("formfac_4D_tslice", "formfac_4D_tslice_px0py0pz0_Nsnk1_x0y1z2t2.h5"),
        join("formfac_4D_tslice", "formfac_4D_tslice_px0py0pz0_Nsnk1_x3y1z2t4.h5"),
    ]
    check_files = [
        join(
            "formfac_4D_tslice_src_avg",
            "formfac_4D_tslice_src_avg_px0py0pz0_Nsnk1_src_avg_0.h5",
        )
    ]

    def command(self):
        """Command which will be executed by the unittest.
        """
        LOGGER.info("Running `average`")
        source_average(
            join(self.tmp_address, "formfac_4D_tslice"),
            overwrite=False,
            expected_sources=["x0y1z2t2"],
            file_name_addition="_0",
        )


class SpecAverageTest(CommandTest, TestCase):
    """Runs average on legacy ``spec_4D`` files and compares results"""

    link_files = [
        join("spec_4D_tslice", "spec_4D_tslice_px0py0pz0_Nsnk1_x0y1z2t2.h5"),
        join("spec_4D_tslice", "spec_4D_tslice_px0py0pz0_Nsnk1_x3y1z2t4.h5"),
    ]
    check_files = [
        join("spec_4D_tslice_avg", "spec_4D_tslice_avg_px0py0pz0_Nsnk1_src_avg.h5")
    ]

    def command(self):
        """Command which will be executed by the unittest.
        """
        LOGGER.info("Running `average`")
        spec_average(
            join(self.tmp_address, "spec_4D_tslice"),
            overwrite=False,
            n_expected_sources=2,
        )


class SpecAverageTestExpectedSources(CommandTest, TestCase):
    """Runs average on ``spec_4D`` files with specified sources and compares results
    """

    link_files = [
        join("spec_4D_tslice", "spec_4D_tslice_px0py0pz0_Nsnk1_x0y1z2t2.h5"),
        join("spec_4D_tslice", "spec_4D_tslice_px0py0pz0_Nsnk1_x3y1z2t4.h5"),
    ]
    check_files = [
        join("spec_4D_tslice_avg", "spec_4D_tslice_avg_px0py0pz0_Nsnk1_src_avg.h5")
    ]

    def command(self):
        """Command which will be executed by the unittest.
        """
        LOGGER.info("Running `average`")
        spec_average(
            join(self.tmp_address, "spec_4D_tslice"),
            overwrite=False,
            expected_sources=["x0y1z2t2", "x3y1z2t4"],
        )


class SpecAverageTestOneExpectedSource(CommandTest, TestCase):
    """Runs average on ``formfac_4D`` files with one specified source and compares res.
    """

    link_files = [
        join("spec_4D_tslice", "spec_4D_tslice_px0py0pz0_Nsnk1_x0y1z2t2.h5"),
        join("spec_4D_tslice", "spec_4D_tslice_px0py0pz0_Nsnk1_x3y1z2t4.h5"),
    ]
    check_files = [
        join("spec_4D_tslice_avg", "spec_4D_tslice_avg_px0py0pz0_Nsnk1_src_avg_0.h5")
    ]

    def command(self):
        """Command which will be executed by the unittest.
        """
        LOGGER.info("Running `average`")
        spec_average(
            join(self.tmp_address, "spec_4D_tslice"),
            overwrite=False,
            expected_sources=["x0y1z2t2"],
            file_name_addition="_0",
        )
