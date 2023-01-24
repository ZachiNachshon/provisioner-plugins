#!/usr/bin/env python3

import unittest
from unittest import mock
from provisioner_features_lib.remote.typer_remote_opts_fakes import TestDataRemoteOpts
from provisioner_single_board_plugin.common.remote.remote_os_configure import RemoteMachineOsConfigureArgs

from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv

from provisioner_single_board_plugin.raspberry_pi.node.configure_cmd import (
    RPiOsConfigureCmd,
    RPiOsConfigureCmdArgs,
)

REMOTE_OS_CONFIGURE_RUNNER_PATH = (
    "provisioner_single_board_plugin.common.remote.remote_os_configure.RemoteMachineOsConfigureRunner"
)

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_single_board_plugin/raspberry_pi/node/configure_cmd_test.py
#
class RPiOsConfigureTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_configure_args(self) -> RPiOsConfigureCmdArgs:
        return RPiOsConfigureCmdArgs(
            remote_opts=TestDataRemoteOpts.create_fake_cli_remote_opts(),
        )

    @mock.patch(f"{REMOTE_OS_CONFIGURE_RUNNER_PATH}.run")
    def test_configure_os_cmd_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        fake_cmd_args = self.create_fake_configure_args()

        RPiOsConfigureCmd().run(ctx=self.env.get_context(), args=fake_cmd_args)
        
        Assertion.expect_call_argument(self, run_call, arg_name="ctx", expected_value=self.env.get_context())
        
        self.assertEqual(
            first=fake_cmd_args.remote_opts, 
            second=run_call.call_args.kwargs["args"].remote_opts
        )

        self.assertEqual(
            first="provisioner_single_board_plugin/raspberry_pi/node/playbooks/configure_os.yaml", 
            second=run_call.call_args.kwargs["args"].ansible_playbook_relative_path_from_root
        )
