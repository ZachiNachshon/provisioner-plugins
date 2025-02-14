#!/usr/bin/env python3

import unittest

import pytest

from provisioner.main import root_menu
from provisioner_shared.test_lib.docker.dockerized import dockerized
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner

#
# !! Run within a Docker container !!
#


# To run these directly from the terminal use:
#  poetry run coverage run -m pytest -s plugins/provisioner_single_board_plugin/provisioner_single_board_plugin/main_test.py --e2e
#
@pytest.mark.e2e
class TestCLI(unittest.TestCase):

    @dockerized(force_build=True)
    def test_examples_plugin_appears_in_menu(self):
        result = TestCliRunner.run(
            root_menu,
            [
                "--help",
            ],
        )
        self.assertIn("single-board  Single boards management as simple as it gets", result)
