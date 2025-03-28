#!/usr/bin/env python3

import unittest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner


# To run these directly from the terminal use:
#  ./run_tests.py plugins/provisioner_single_board_plugin/provisioner_single_board_plugin/main_test.py
#
class TestCLI(unittest.TestCase):

    def test_single_board_plugin_appears_in_menu(self):
        result = TestCliRunner.run(
            root_menu,
            [
                "--help",
            ],
        )
        self.assertIn("single-board", result)
        self.assertIn("Single boards management as simple as it gets", result)
