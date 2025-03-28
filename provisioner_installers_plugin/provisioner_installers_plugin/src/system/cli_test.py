# !/usr/bin/env python3

import unittest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner


# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_installers_plugin/provisioner_installers_plugin/src/system/cli_test.py
#
class UtilityInstallerSystemTestShould(unittest.TestCase):

    def test_system_utils_prints_to_menu_as_expected(self) -> None:
        output = TestCliRunner.run(
            root_menu,
            [
                "install",
                "system",
            ],
        )
        self.assertIn("python  Install Python / pip package manager", output)
