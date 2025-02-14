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
#  poetry run coverage run -m pytest -s plugins/provisioner_examples_plugin/provisioner_examples_plugin/src/ansible/hello_world_e2e.py --e2e
#
@pytest.mark.e2e
class TestCLI(unittest.TestCase):

    @dockerized(force_build=True)
    def test_e2e_examples_hello_world_command_run_successfully(self):
        result = TestCliRunner.run(
            root_menu,
            [
                "examples",
                "ansible",
                "hello",
                "--username",
                "TestUser",
            ],
        )
        self.assertIn("Hello Test User !", result)
