"""Base module for legacy file tests

The logic of the tests are the same:
1. Run a bash command corresponding to a ``nucelff`` script
2. Check if the right folders and files have been created
3. Check if the file match the legacy files.
"""
import os

from tempfile import TemporaryDirectory

from nucleon_elastic_ff.utilities import set_up_logger
from nucleon_elastic_ff.data.h5io import assert_h5files_equal


LOGFILE = "nucleon_elastic_ff_test"
LOGGER = set_up_logger(LOGFILE, mode="w")

TMPDIR = os.path.join(os.getcwd(), "tests")

DATAROOT = os.path.join(os.getcwd(), "data")


class CommandTest:
    """Abstract class which creates temporary dirs, runs a command, checks output and
    deletes tmp files.
    """

    link_files = []
    check_files = []
    atol: float = 0.0
    rtol: float = 1.0e-8

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tmp_dir = None

    @staticmethod
    def command():
        """Command which will be executed by the unittest.
        """
        LOGGER.info("Running command")

    def test_01_check_command(self):
        """Runs the command and checks the files
        """
        LOGGER.info("Running `command`")
        self.command()

        LOGGER.info("Checking created files")
        for file in self.check_files:
            created_path = os.path.join(self.tmp_address, file)
            expected_path = os.path.join(DATAROOT, file)

            LOGGER.info("\t%s", created_path)

            assert_h5files_equal(
                created_path, expected_path, atol=self.atol, rtol=self.rtol
            )
            LOGGER.info("\tFiles agree")

    @property
    def tmp_address(self):
        """Returns address of temporary folder.
        """
        return self._tmp_dir.name

    def setUp(self):  # pylint: disable=C0103
        """Creates all required directories and links all required files
        """
        self._tmp_dir = TemporaryDirectory(dir=TMPDIR)
        LOGGER.info("Created temporary dir `%s` exists", self.tmp_address)

        for file in self.link_files:
            target_path = os.path.join(self.tmp_address, file)
            target_dir = os.path.dirname(target_path)
            if not os.path.exists(target_dir):
                LOGGER.info("Creating `%s`", target_dir)
                os.makedirs(target_dir)

            source_path = os.path.join(DATAROOT, file)
            LOGGER.info("Linking `%s` ->  `%s` ", source_path, target_path)
            os.link(source_path, target_path)

    def tearDown(self):  # pylint: disable=R0912, C0103
        """Deletes all created and all linked directories and files
        """
        LOGGER.info("Removing temporary dir `%s`", self.tmp_address)
        self._tmp_dir.cleanup()
