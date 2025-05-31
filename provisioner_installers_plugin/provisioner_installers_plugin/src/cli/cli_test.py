# !/usr/bin/env python3

import re
import unittest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner

INSTALLER_CMD_MODULE_PATH = "provisioner_installers_plugin.src.installer.cmd.installer_cmd"


# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_installers_plugin/provisioner_installers_plugin/src/cli/cli_test.py
#
class UtilityInstallerCliTestShould(unittest.TestCase):

    def test_cli_utilities_prints_to_menu_as_expected(self) -> None:
        result = TestCliRunner.run_throws_not_managed(
            root_menu,
            [
                "install",
                "cli",
            ],
        )
        
        # Use regex to match command descriptions with flexible spacing
        anchor_pattern = re.compile(r'anchor\s+Create Dynamic CLI\'s as your GitOps Marketplace')
        helm_pattern = re.compile(r'helm\s+Package Manager for Kubernetes')
        
        self.assertIsNotNone(anchor_pattern.search(result.output))
        self.assertIsNotNone(helm_pattern.search(result.output))
