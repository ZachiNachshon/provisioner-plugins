#!/usr/bin/env python3

import unittest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner


# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_examples_plugin/provisioner_examples_plugin/src/ansible/cli_test.py
#
class AnsibleCliTestShould(unittest.TestCase):

    def test_ansible_cmds_prints_to_menu_as_expected(self) -> None:
        output = TestCliRunner.run(root_menu, ["examples", "ansible"])
        self.assertIn("hello  Run a dummy hello world scenario locally", output)
