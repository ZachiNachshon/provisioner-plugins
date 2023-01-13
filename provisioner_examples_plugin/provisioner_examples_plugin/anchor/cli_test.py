#!/usr/bin/env python3

import unittest
from unittest import mock

from typer.testing import CliRunner

from provisioner_examples_plugin.main_fake import get_fake_app

runner = CliRunner()

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_examples_plugin/anchor/cli_test.py
#
class AnchorCliTestShould(unittest.TestCase):
    @mock.patch("provisioner_examples_plugin.anchor.anchor_cmd.AnchorCmd.run")
    def test_cli_anchor_cmd_with_args_success(self, run_call: mock.MagicMock) -> None:
        expected_anchor_run_command = "run --action=test-action"
        expected_github_organization = "test-org"
        expected_repository_name = "test-repo"
        expected_branch_name = "test-branch"
        expected_github_access_token = "test-github-access-token"
        
        result = runner.invoke(
            get_fake_app(),
            ["--dry-run", "--verbose", "examples", "anchor", "run-command", 
            f"--anchor-run-command={expected_anchor_run_command}",
            f"--github-organization={expected_github_organization}",
            f"--repository-name={expected_repository_name}",
            f"--branch-name={expected_branch_name}",
            f"--github-access-token={expected_github_access_token}",
            ],
        )
        self.assertEqual(1, run_call.call_count)

        run_call_kwargs = run_call.call_args.kwargs
        ctx = run_call_kwargs["ctx"]
        call_args = run_call_kwargs["args"]

        self.assertIsNotNone(ctx)
        self.assertIsNotNone(call_args)
        self.assertEqual(call_args.anchor_run_command, expected_anchor_run_command)
        self.assertEqual(call_args.github_organization, expected_github_organization)
        self.assertEqual(call_args.repository_name, expected_repository_name)
        self.assertEqual(call_args.branch_name, expected_branch_name)
        self.assertEqual(call_args.github_access_token, expected_github_access_token)
