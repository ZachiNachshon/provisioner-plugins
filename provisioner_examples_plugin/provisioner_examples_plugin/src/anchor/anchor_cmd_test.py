#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_examples_plugin.src.anchor.anchor_cmd import AnchorCmd, AnchorCmdArgs
from provisioner_shared.components.remote.remote_opts_fakes import TestDataRemoteOpts
from provisioner_shared.components.vcs.vcs_opts_fakes import TestDataVersionControlOpts
from provisioner_shared.test_lib.assertions import Assertion
from provisioner_shared.test_lib.test_env import TestEnv

ANCHOR_RUN_COMMAND_RUNNER_PATH = "provisioner_shared.components.anchor.anchor_runner.AnchorCmdRunner"

EXPECTED_ANCHOR_RUN_COMMAND = "run --action=test-action"
EXPECTED_GITHUB_ORGANIZATION = "test-org"
EXPECTED_REPOSITORY_NAME = "test-repo"
EXPECTED_BRANCH_NAME = "test-branch"
EXPECTED_GIT_ACCESS_TOKEN = "test-git-access-token"


#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest plugins/provisioner_examples_plugin/provisioner_examples_plugin/src/anchor/anchor_cmd_test.py
#
class AnchorCmdTestShould(unittest.TestCase):
    @mock.patch(f"{ANCHOR_RUN_COMMAND_RUNNER_PATH}.run")
    def test_anchor_cmd_run_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        ctx = env.get_context()
        fake_vcs_cfg = TestDataVersionControlOpts().create_fake_cli_vcs_opts()
        fake_remote_cfg = TestDataRemoteOpts().create_fake_cli_remote_opts()

        def assertion_callback(args):
            self.assertEqual(EXPECTED_ANCHOR_RUN_COMMAND, args.anchor_run_command)
            self.assertEqual(fake_vcs_cfg, args.vcs_opts)
            self.assertEqual(fake_remote_cfg, args.remote_opts)

        AnchorCmd().run(
            ctx=ctx,
            args=AnchorCmdArgs(
                anchor_run_command=EXPECTED_ANCHOR_RUN_COMMAND,
                vcs_opts=fake_vcs_cfg,
                remote_opts=fake_remote_cfg,
            ),
        )
        Assertion.expect_call_argument(self, run_call, arg_name="ctx", expected_value=env.get_context())
        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
