#!/usr/bin/env python3

import re
import unittest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner


# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_examples_plugin/provisioner_examples_plugin/src/ansible/cli_test.py
#
class AnsibleCliTestShould(unittest.TestCase):

    def test_ansible_cmds_prints_to_menu_as_expected(self) -> None:
        result = TestCliRunner.run_throws_not_managed(root_menu, ["examples", "ansible"])
        
        # Use regex to match command description with flexible spacing
        hello_pattern = re.compile(r'hello\s+Run a dummy hello world scenario locally')
        
        self.assertIsNotNone(hello_pattern.search(result.output))
