"""Compares tsliced routines against results used for export.
"""
from os.path import join

from unittest import TestCase

from nucleon_elastic_ff.test_utilities import CommandTest
from nucleon_elastic_ff.test_utilities import LOGGER

from nucleon_elastic_ff.data.scripts.tslice import tslice


class FormfacTsliceTest(CommandTest, TestCase):
    """Runs tslice on legacy ``formfac_4D`` files and compares results"""

    link_files = [
        join("formfac_4D", "formfac_4D_px0py0pz0_Nsnk1_x0y1z2t2.h5"),
        join("formfac_4D", "formfac_4D_px0py0pz0_Nsnk1_x3y1z2t4.h5"),
    ]
    check_files = [
        join("formfac_4D_tslice", "formfac_4D_tslice_px0py0pz0_Nsnk1_x0y1z2t2.h5"),
        join("formfac_4D_tslice", "formfac_4D_tslice_px0py0pz0_Nsnk1_x3y1z2t4.h5"),
    ]

    def command(self):
        """Command which will be executed by the unittest.
        """
        LOGGER.info("Running `tslice`")
        tslice(
            join(self.tmp_address, "formfac_4D"),
            overwrite=False,
            boundary_sign_flip=False,
        )


class SpecTsliceTest(CommandTest, TestCase):
    """Runs tslice on legacy ``spec_4D`` files and compares results"""

    link_files = [
        join("spec_4D", "spec_4D_px0py0pz0_Nsnk1_x0y1z2t2.h5"),
        join("spec_4D", "spec_4D_px0py0pz0_Nsnk1_x3y1z2t4.h5"),
    ]
    check_files = [
        join("spec_4D_tslice", "spec_4D_tslice_px0py0pz0_Nsnk1_x0y1z2t2.h5"),
        join("spec_4D_tslice", "spec_4D_tslice_px0py0pz0_Nsnk1_x3y1z2t4.h5"),
    ]

    def command(self):
        """Command which will be executed by the unittest.
        """
        LOGGER.info("Running `tslice`")
        tslice(
            join(self.tmp_address, "spec_4D"),
            name_input="spec_4D",
            name_output="spec_4D_tslice",
            overwrite=False,
            tslice_fact=0.5,
            dset_patterns=["4D_correlator/x[0-9]+_y[0-9]+_z[0-9]+_t[0-9]+"],
            boundary_sign_flip=True,
        )
