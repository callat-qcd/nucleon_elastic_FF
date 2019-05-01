"""Base module for legacy file tests

The logic of the tests are the same:
1. Run a bash command corresponding to a ``nucelff`` script
2. Check if the right folders and files have been created
3. Check if the file match the legacy files.
"""
import os
import subprocess

from unittest import TestCase

from nucleon_elastic_ff.utilities import set_up_logger
from nucleon_elastic_ff.data.h5io import assert_h5files_equal


LOGFILE = "nucleon_elastic_ff_test"
LOGGER = set_up_logger(LOGFILE, mode="w")

TMPDIR = os.path.join(os.getcwd(), "tests", "temp")

DATAROOT = os.path.join(os.getcwd(), "data")


class CommandTest(TestCase):
    """Abstract class which creates temporary dirs, runs a command, checks output and
    deletes tmp files.
    """

    link_files = {}
    check_files = {}
    command = []
    atol = 0.0
    rtol = 1.0e-8

    def check_command(self):
        """Runs the command and checks the files
        """
        LOGGER.info("Running `%s`", " ".join(self.command))
        process = subprocess.Popen(self.command, stdout=subprocess.PIPE)
        process.communicate()

        LOGGER.info("Checking created files")
        for expected, created in self.check_files.items():
            created_path = os.path.join(TMPDIR, created)
            expected_path = os.path.join(DATAROOT, expected)

            LOGGER.info("\t%s", created_path)
            self.assertTrue(
                os.path.exists(created_path), msg="Could not locate `%s`" % created_path
            )
            assert_h5files_equal(
                created_path, expected_path, atol=self.atol, rtol=self.rtol
            )

    def setUp(self):  # pylint: disable=C0103
        """Creates all required directories and links all required files
        """
        LOGGER.info("Checking if temp dir `%s` exists", TMPDIR)
        if not os.path.exists(TMPDIR):
            LOGGER.info("Creating temp dir `%s`", TMPDIR)
            os.makedirs(TMPDIR)

        for source, target in self.link_files:
            target_path = os.path.join(TMPDIR, target)
            target_dir = os.path.dirname(target_path)
            if not os.path.exists(target_dir):
                LOGGER.info("Creating `%s`", target_dir)
                os.makedirs(TMPDIR)

            source_path = os.path.join(DATAROOT, source)
            LOGGER.info("Linking `%s` ->  `%s` ", source_path, target_path)
            os.link(source_path, target_path)

    def tearDown(self):  # pylint: disable=R0912, C0103
        """Deletes all created and all linked directories and files
        """
        for target in self.link_files.values():
            target_path = os.path.join(TMPDIR, target)
            LOGGER.info("Removing `%s`", target_path)
            if TMPDIR in target_path and not DATAROOT in target_path:
                os.remove(target_path)
            else:
                raise ValueError(
                    "Trying to remove non temporary file `%s`." % target_path
                    + " Check the `link_files` of the test!"
                )

        for created in self.check_files.values():
            created_path = os.path.join(TMPDIR, created)
            LOGGER.info("Removing `%s`", created_path)
            if TMPDIR in created_path and not DATAROOT in created_path:
                os.remove(created_path)
            else:
                raise ValueError(
                    "Trying to remove non temporary file `%s`." % created_path
                    + " Check the `check_files` of the test!"
                )

        for target in self.link_files.values():
            target_path = os.path.join(TMPDIR, target)
            target_dir = os.path.dirname(target_path)
            if os.path.exists(target_dir):
                LOGGER.info("Removing `%s`", target_dir)
                if TMPDIR in target_dir and not DATAROOT in target_dir:
                    os.removedirs(target_dir)
                else:
                    raise ValueError(
                        "Trying to remove non temporary folder `%s`." % target_dir
                        + " Check the `link_files` of the test!"
                    )

        for created in self.check_files.values():
            created_path = os.path.join(TMPDIR, created)
            created_dir = os.path.dirname(created_path)
            if os.path.exists(created_dir):
                LOGGER.info("Removing `%s`", created_dir)
                if TMPDIR in created_dir and not DATAROOT in created_dir:
                    os.removedirs(created_dir)
                else:
                    raise ValueError(
                        "Trying to remove non temporary folder `%s`." % created_dir
                        + " Check the `link_files` of the test!"
                    )

        LOGGER.info("Checking if temp dir `%s` exists", TMPDIR)
        if os.path.exists(TMPDIR):
            LOGGER.info("Removing temp dir `%s`", TMPDIR)
            os.removedirs(TMPDIR)
