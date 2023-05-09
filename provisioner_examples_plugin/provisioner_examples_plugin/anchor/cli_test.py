#!/usr/bin/env python3

import unittest
from unittest import mock

from python_core_lib.test_lib.assertions import Assertion
from typer.testing import CliRunner

from provisioner_examples_plugin.main_fake import get_fake_app

EXPECTED_ANCHOR_RUN_COMMAND = "run --action=test-action"
EXPECTED_GITHUB_ORGANIZATION = "test-org"
EXPECTED_REPOSITORY_NAME = "test-repo"
EXPECTED_BRANCH_NAME = "test-branch"
EXPECTED_GITHUB_ACCESS_TOKEN = "test-github-access-token"

ANCHOR_COMMAND_PATH = "provisioner_examples_plugin.anchor.anchor_cmd.AnchorCmd"

runner = CliRunner()

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_examples_plugin/anchor/cli_test.py
#
class AnchorCliTestShould(unittest.TestCase):
    @mock.patch(f"{ANCHOR_COMMAND_PATH}.run")
    def test_cli_anchor_cmd_with_args_success(self, run_call: mock.MagicMock) -> None:
        runner.invoke(
            get_fake_app(),
            [
                "--dry-run",
                "--verbose",
                "examples",
                "anchor",
                "run-command",
                f"--anchor-run-command={EXPECTED_ANCHOR_RUN_COMMAND}",
                f"--github-organization={EXPECTED_GITHUB_ORGANIZATION}",
                f"--repository-name={EXPECTED_REPOSITORY_NAME}",
                f"--branch-name={EXPECTED_BRANCH_NAME}",
                f"--github-access-token={EXPECTED_GITHUB_ACCESS_TOKEN}",
            ],
        )

        def assertion_callback(args):
            self.assertEqual(EXPECTED_ANCHOR_RUN_COMMAND, args.anchor_run_command)
            self.assertEqual(EXPECTED_GITHUB_ORGANIZATION, args.github_organization)
            self.assertEqual(EXPECTED_REPOSITORY_NAME, args.repository_name)
            self.assertEqual(EXPECTED_BRANCH_NAME, args.branch_name)
            self.assertEqual(EXPECTED_GITHUB_ACCESS_TOKEN, args.github_access_token)

        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
