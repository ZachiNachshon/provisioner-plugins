#!/usr/bin/env python3

import unittest

import pytest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner


# To run these directly from the terminal use:
#  poetry run coverage run -m pytest -s plugins/provisioner_installers_plugin/provisioner_installers_plugin/main_test.py
#
class TestCLI(unittest.TestCase):

    def test_installers_plugin_appears_in_menu(self):
        result = TestCliRunner.run(
            root_menu,
            [
                "--help",
            ],
        )
        self.assertIn("install       Install anything anywhere on any OS/Arch", result)
