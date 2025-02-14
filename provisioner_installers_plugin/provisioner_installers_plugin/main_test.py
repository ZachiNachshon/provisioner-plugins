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
#  poetry run coverage run -m pytest -s plugins/provisioner_installers_plugin/provisioner_installers_plugin/main_test.py --e2e
#
@pytest.mark.e2e
class TestCLI(unittest.TestCase):

    @dockerized()
    def test_installers_plugin_appears_in_menu(self):
        result = TestCliRunner.run(
            root_menu,
            [
                "--help",
            ],
        )
        self.assertIn("install       Install anything anywhere on any OS/Arch", result)
