# !/usr/bin/env python3

import re
import unittest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner


# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_installers_plugin/provisioner_installers_plugin/src/system/cli_test.py
#
class UtilityInstallerSystemTestShould(unittest.TestCase):

    def test_system_utils_prints_to_menu_as_expected(self) -> None:
        result = TestCliRunner.run_throws_not_managed(
            root_menu,
            [
                "install",
                "system",
            ],
        )

        # Use regex to match command description with flexible spacing
        python_pattern = re.compile(r"python\s+Install Python / pip package manager")

        self.assertIsNotNone(python_pattern.search(result.output))
