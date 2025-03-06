#!/usr/bin/env python3

import unittest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner


# To run these directly from the terminal use:
#  poetry run coverage run -m pytest -s plugins/provisioner_examples_plugin/provisioner_examples_plugin/main_test.py
#
class TestCLI(unittest.TestCase):

    def test_examples_plugin_appears_in_menu(self):
        result = TestCliRunner.run(
            root_menu,
            [
                "--help",
            ],
        )
        self.assertIn("examples      Playground for using the CLI framework", result)
