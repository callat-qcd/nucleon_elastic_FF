"""Compares tsliced routines against results used for export.
"""
from os.path import join

from unittest import TestCase

from nucleon_elastic_ff.test_utilities import CommandTest
from nucleon_elastic_ff.test_utilities import TMPDIR
from nucleon_elastic_ff.test_utilities import LOGGER

from nucleon_elastic_ff.data.scripts.fft import fft_file


class FormfacFFTTest(CommandTest, TestCase):
    """Runs fft on legacy ``formfac_4D`` files and compares results"""

    link_files = [
        join(
            "formfac_4D_tslice_src_avg",
            "formfac_4D_tslice_src_avg_px0py0pz0_Nsnk1_src_avg.h5",
        )
    ]
    check_files = [
        join(
            "formfac_4D_tslice_src_avg",
            "formfac_4D_tslice_src_avg_px0py0pz0_Nsnk1_src_avg_fft.h5",
        )
    ]

    @staticmethod
    def command():
        """Command which will be executed by the unittest.
        """
        LOGGER.info("Running `fft`")
        fft_file(
            join(
                TMPDIR,
                "formfac_4D_tslice_src_avg",
                "formfac_4D_tslice_src_avg_px0py0pz0_Nsnk1_src_avg.h5",
            ),
            join(
                TMPDIR,
                "formfac_4D_tslice_src_avg",
                "formfac_4D_tslice_src_avg_px0py0pz0_Nsnk1_src_avg_fft.h5",
            ),
            overwrite=False,
            max_momentum=2,
            cuda=False,
        )


class FormfacChunkedFFTTest(CommandTest, TestCase):
    """Runs chunked fft on legacy ``formfac_4D`` files and compares results"""

    link_files = [
        join(
            "formfac_4D_tslice_src_avg",
            "formfac_4D_tslice_src_avg_px0py0pz0_Nsnk1_src_avg.h5",
        )
    ]
    check_files = [
        join(
            "formfac_4D_tslice_src_avg",
            "formfac_4D_tslice_src_avg_px0py0pz0_Nsnk1_src_avg_fft.h5",
        )
    ]

    @staticmethod
    def command():
        """Command which will be executed by the unittest.
        """
        LOGGER.info("Running `fft`")
        fft_file(
            join(
                TMPDIR,
                "formfac_4D_tslice_src_avg",
                "formfac_4D_tslice_src_avg_px0py0pz0_Nsnk1_src_avg.h5",
            ),
            join(
                TMPDIR,
                "formfac_4D_tslice_src_avg",
                "formfac_4D_tslice_src_avg_px0py0pz0_Nsnk1_src_avg_fft.h5",
            ),
            overwrite=False,
            max_momentum=2,
            chunk_size=2,
            cuda=False,
        )


class SpecFFTTest(CommandTest, TestCase):
    """Runs fft on legacy ``spec_4D`` files and compares results"""

    link_files = [
        join("spec_4D_tslice_avg", "spec_4D_tslice_avg_px0py0pz0_Nsnk1_src_avg.h5")
    ]
    check_files = [
        join("spec_4D_tslice_avg", "spec_4D_tslice_avg_px0py0pz0_Nsnk1_src_avg_fft.h5")
    ]

    @staticmethod
    def command():
        """Command which will be executed by the unittest.
        """
        LOGGER.info("Running `fft`")
        fft_file(
            join(
                TMPDIR,
                "spec_4D_tslice_avg",
                "spec_4D_tslice_avg_px0py0pz0_Nsnk1_src_avg.h5",
            ),
            join(
                TMPDIR,
                "spec_4D_tslice_avg",
                "spec_4D_tslice_avg_px0py0pz0_Nsnk1_src_avg_fft.h5",
            ),
            overwrite=False,
            max_momentum=2,
            cuda=False,
        )
