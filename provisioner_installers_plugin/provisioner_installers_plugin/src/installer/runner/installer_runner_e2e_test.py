#!/usr/bin/env python3

import unittest

import pytest

from provisioner.main import root_menu
from provisioner_shared.test_lib.cli_container import RemoteSSHContainer
from provisioner_shared.test_lib.docker.skip_if_not_docker import skip_if_not_in_docker
from provisioner_shared.test_lib.test_cli_runner import CliTestRunnerConfig, TestCliRunner


# To run these directly from the terminal use:
#  ./run-tests.py plugins/provisioner_installers_plugin/provisioner_installers_plugin/src/installer/runner/installer_runner_e2e_test.py --only-e2e
#
@pytest.mark.e2e
class HelloWorldE2ETestShould(unittest.TestCase):

    # Run before each test
    @classmethod
    def setUpClass(cls):
        """Start the container once before any tests in this class."""
        cls.container = RemoteSSHContainer()
        cls.container.start()

    # Stop after each test
    @classmethod
    def tearDownClass(cls):
        """Stop the container after all tests in this class have completed."""
        if cls.container:
            cls.container.stop()
            cls.container = None  # Ensure cleanup

    @skip_if_not_in_docker
    def test_e2e_install_anchor_on_local_successfully(self):
        output = TestCliRunner.run(
            root_menu,
            [
                "install",
                "--environment",
                "Local",
                "cli",
                "anchor@v0.10.0",
                "-vy",
            ],
        )
        self.assertIn("Successfully installed utility", output)
        self.assertIn("name:    anchor", output)
        self.assertIn("version: v0.10.0", output)
        self.assertIn("binary:  /root/.local/bin/anchor", output)

    def test_e2e_install_anchor_on_remote_successfully(self):
        output = TestCliRunner.run(
            root_menu,
            [
                "install",
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
                "cli",
                "anchor@v0.10.0",
                "--package-manager",
                "uv",
                "-vy",
            ],
            test_cfg=CliTestRunnerConfig(is_installer_plugin_test=True),
        )
        self.assertIn("Successfully installed utility", output)
        self.assertIn("name:    anchor", output)
        self.assertIn("version: v0.10.0", output)
        self.assertIn("binary:  /home/pi/.local/bin/anchor", output)
