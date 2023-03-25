#!/usr/bin/env python3

import unittest
from unittest import mock

from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv

from provisioner_examples_plugin.anchor.anchor_cmd import AnchorCmd, AnchorCmdArgs

ANCHOR_RUN_COMMAND_RUNNER_PATH = "provisioner_features_lib.anchor.anchor_runner.AnchorCmdRunner"

EXPECTED_ANCHOR_RUN_COMMAND = "run --action=test-action"
EXPECTED_GITHUB_ORGANIZATION = "test-org"
EXPECTED_REPOSITORY_NAME = "test-repo"
EXPECTED_BRANCH_NAME = "test-branch"
EXPECTED_GITHUB_ACCESS_TOKEN = "test-github-access-token"

#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest provisioner_examples_plugin/anchor/anchor_cmd_test.py
#
class AnchorCmdTestShould(unittest.TestCase):
    @mock.patch(f"{ANCHOR_RUN_COMMAND_RUNNER_PATH}.run")
    def test_anchor_cmd_run_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        ctx = env.get_context()

        def assertion_callback(args):
            self.assertEqual(EXPECTED_ANCHOR_RUN_COMMAND, args.anchor_run_command)
            self.assertEqual(EXPECTED_GITHUB_ORGANIZATION, args.github_organization)
            self.assertEqual(EXPECTED_REPOSITORY_NAME, args.repository_name)
            self.assertEqual(EXPECTED_BRANCH_NAME, args.branch_name)
            self.assertEqual(EXPECTED_GITHUB_ACCESS_TOKEN, args.github_access_token)

        AnchorCmd().run(
            ctx=ctx,
            args=AnchorCmdArgs(
                anchor_run_command=EXPECTED_ANCHOR_RUN_COMMAND,
                github_organization=EXPECTED_GITHUB_ORGANIZATION,
                repository_name=EXPECTED_REPOSITORY_NAME,
                branch_name=EXPECTED_BRANCH_NAME,
                github_access_token=EXPECTED_GITHUB_ACCESS_TOKEN,
            ),
        )
        Assertion.expect_call_argument(self, run_call, arg_name="ctx", expected_value=env.get_context())
        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
