#!/usr/bin/env python3

import unittest

import pytest

from provisioner.main import root_menu
from provisioner_shared.test_lib.rpi_os_container import RemoteRPiOsContainer
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner
from provisioner_shared.test_lib.test_env import TestEnv

# To run as a single test target:
#  ./run_tests.py plugins/provisioner_single_board_plugin/provisioner_single_board_plugin/src/raspberry_pi/node/cli_e2e_test.py
#
@pytest.mark.e2e
class RaspberryPiNodeCliE2ETestShould(unittest.TestCase):
    env = TestEnv.create()

    # Run before each test
    @classmethod
    def setUpClass(cls):
        """Start the container once before any tests in this class."""
        cls.container = RemoteRPiOsContainer()
        cls.container.start()

    # Stop after each test
    @classmethod
    def tearDownClass(cls):
        """Stop the container after all tests in this class have completed."""
        if cls.container:
            cls.container.stop()
            cls.container = None  # Ensure cleanup

    def test_e2e_install_anchor_on_remote_successfully(self):
        output = TestCliRunner.run(
            root_menu,
            [
                "single-board",
                "raspberry-pi",
                "node",
                "--environment",
                "Remote",
                "--connect-mode",
                "Flags",
                "--node-username",
                "pi",
                "--node-password",
                "raspberry",
                "--ip-address",
                "127.0.0.1",
                "--port",
                "2222",
                "--hostname",
                "test-node",
                "--verbosity",
                "Verbose",
                "-vy",
                "configure",
                # TODO: add the following flags to the command
                # "--host", "test_host",
                # "--hostname", "test-rpi",
                # "--boot-behaviour", "B1",  # Boot to CLI & require login
                # "--ssh", "0",  # Enable SSH
                # "--camera", "1",  # Disable camera
                # "--spi", "1",  # Disable SPI
                # "--i2c", "1",  # Disable I2C
                # "--serial-bus", "1",  # Disable serial bus
            ],
        )

        self.assertIn("Mock raspi-config: do_boot_behaviour B1", output)
        self.assertIn("Mock raspi-config: do_ssh 0", output)
        self.assertIn("Mock raspi-config: do_camera 1", output)
        self.assertIn("Mock raspi-config: do_spi 1", output)
        self.assertIn("Mock raspi-config: do_i2c 1", output)
        self.assertIn("Mock raspi-config: do_serial 1", output)
