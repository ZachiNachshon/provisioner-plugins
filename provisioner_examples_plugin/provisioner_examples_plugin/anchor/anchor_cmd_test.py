#!/usr/bin/env python3

import unittest
from unittest import mock

from python_core_lib.infra.context import Context
from python_core_lib.utils.os import MAC_OS, OsArch

from provisioner_examples_plugin.anchor.anchor_cmd import AnchorCmd, AnchorCmdArgs


#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest provisioner_examples_plugin/anchor/anchor_cmd_test.py
#
class AnchorCmdTestShould(unittest.TestCase):
    @mock.patch("provisioner_features_lib.anchor.anchor_runner.AnchorCmdRunner.run")
    def test_anchor_cmd_run_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        expected_anchor_run_command = "run --action=test-action"
        expected_github_organization = "test-org"
        expected_repository_name = "test-repo"
        expected_branch_name = "test-branch"
        expected_github_access_token = "test-github-access-token"

        args = AnchorCmdArgs(
            anchor_run_command=expected_anchor_run_command,
            github_organization=expected_github_organization,
            repository_name=expected_repository_name,
            branch_name=expected_branch_name,
            github_access_token=expected_github_access_token,
        )

        cmd = AnchorCmd()
        cmd.run(ctx=ctx, args=args)

        run_call_kwargs = run_call.call_args.kwargs
        ctx_call_arg = run_call_kwargs["ctx"]
        cmd_call_args = run_call_kwargs["args"]

        self.assertEqual(ctx, ctx_call_arg)
        self.assertEqual(expected_anchor_run_command, cmd_call_args.anchor_run_command)
        self.assertEqual(expected_github_organization, cmd_call_args.github_organization)
        self.assertEqual(expected_repository_name, cmd_call_args.repository_name)
        self.assertEqual(expected_branch_name, cmd_call_args.branch_name)
        self.assertEqual(expected_github_access_token, cmd_call_args.github_access_token)
