# !/usr/bin/env python3

import unittest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner

INSTALLER_CMD_MODULE_PATH = "provisioner_installers_plugin.src.installer.cmd.installer_cmd"


# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_installers_plugin/provisioner_installers_plugin/src/cli/cli_test.py
#
class UtilityInstallerCliTestShould(unittest.TestCase):

    def test_cli_utilities_prints_to_menu_as_expected(self) -> None:
        output = TestCliRunner.run(
            root_menu,
            [
                "install",
                "cli",
            ],
        )
        self.assertIn("anchor    Create Dynamic CLI's as your GitOps Marketplace", output)
        self.assertIn("helm      Package Manager for Kubernetes", output)
