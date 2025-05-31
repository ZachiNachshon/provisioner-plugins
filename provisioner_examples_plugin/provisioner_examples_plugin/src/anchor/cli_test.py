#!/usr/bin/env python3

import re
import unittest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner


# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_examples_plugin/provisioner_examples_plugin/src/anchor/cli_test.py
#
class AnchorCliTestShould(unittest.TestCase):

    def test_anchor_cmds_prints_to_menu_as_expected(self) -> None:
        result = TestCliRunner.run_throws_not_managed(root_menu, ["examples", "anchor"])
        
        print(f"Actual output:\n{result.output}")
        print(f"Exit code: {result.exit_code}")
        
        # Use flexible regex that matches the core description - handle CI/local differences
        run_command_pattern = re.compile(r'run-command\s+Run a dummy anchor run scenario locally')
        
        self.assertIsNotNone(run_command_pattern.search(result.output))
