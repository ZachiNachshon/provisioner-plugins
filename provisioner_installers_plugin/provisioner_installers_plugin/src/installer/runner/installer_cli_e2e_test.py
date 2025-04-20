#!/usr/bin/env python3

import os
import unittest

import pytest

from provisioner.main import root_menu
from provisioner_shared.test_lib.cli_container import RemoteSSHContainer
from provisioner_shared.test_lib.docker.skip_if_not_docker import skip_if_not_in_docker
from provisioner_shared.test_lib.test_cli_runner import CliTestRunnerConfig, TestCliRunner


# To run these directly from the terminal use:
#  ./run_tests.py plugins/provisioner_installers_plugin/provisioner_installers_plugin/src/installer/runner/installer_cli_e2e_test.py --only-e2e
#
@pytest.mark.e2e
class InstallerCliE2ETestShould(unittest.TestCase):

    # Run before each test
    @classmethod
    def setUpClass(cls):
        """Start the container once before any tests in this class."""
        os.environ["PROVISIONER_INSTALLER_PLUGIN_TEST"] = "true"
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
    def test_e2e_install_uninstall_anchor_on_local_successfully(self):
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

        output = TestCliRunner.run(
            root_menu,
            [
                "install",
                "--environment",
                "Local",
                "cli",
                "anchor",
                "--uninstall",
                "-vy",
            ],
        )
        self.assertIn("Uninstalling utility: anchor", output)
        self.assertIn(f"Removing symlink at {os.path.expanduser('~/.local/bin/anchor')}", output)
        self.assertIn(f"Removing binary directory at {os.path.expanduser('~/.config/provisioner/binaries/anchor')}", output)

    def test_e2e_install_uninstall_anchor_on_remote_successfully(self):
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
                "anchor",
                "--uninstall",
                "--package-manager",
                "uv",
                "-vy",
            ],
            test_cfg=CliTestRunnerConfig(is_installer_plugin_test=True),
        )
        self.assertIn("Uninstalling utility: anchor", output)
        self.assertIn(f"Removing symlink at /home/pi/.local/bin/anchor", output)
        self.assertIn(f"Removing binary directory at /home/pi/.config/provisioner/binaries/anchor", output)