#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_installers_plugin.src.installer.cmd.installer_cmd import (
    UtilityInstallerCmd,
    UtilityInstallerCmdArgs,
)
from provisioner_installers_plugin.src.installer.domain.command import InstallerSubCommandName
from provisioner_installers_plugin.src.installer.domain.dynamic_args import DynamicArgs
from provisioner_installers_plugin.src.installer.runner.installer_runner import (
    UtilityInstallerRunnerCmdArgs,
)
from provisioner_installers_plugin.src.utilities.utilities_cli import SupportedToolingsCli

from provisioner_shared.components.remote.remote_opts_fakes import TestDataRemoteOpts
from provisioner_shared.test_lib.assertions import Assertion
from provisioner_shared.test_lib.test_env import TestEnv

UTILITY_INSTALLER_CMD_RUNNER_PATH = (
    "provisioner_installers_plugin.src.installer.runner.installer_runner.UtilityInstallerCmdRunner"
)

DYNAMIC_ARGS_DICT = {
    "first-key": "first-val",
    "second-key": "second-val",
}


# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_installers_plugin/provisioner_installers_plugin/src/installer/cmd/installer_cmd_test.py
#
class UtilityInstallerCmdTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_utility_installer_args(self) -> UtilityInstallerCmdArgs:
        return UtilityInstallerCmdArgs(
            utils_to_install=["anchor", "k3s-agent"],
            dynamic_args=DYNAMIC_ARGS_DICT,
            sub_command_name=InstallerSubCommandName.CLI,
            git_access_token="test-git-access-token",
            remote_opts=TestDataRemoteOpts.create_fake_cli_remote_opts(),
        )

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}.run")
    def test_utility_install_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        fake_cmd_args = self.create_fake_utility_installer_args()

        UtilityInstallerCmd().run(ctx=self.env.get_context(), args=fake_cmd_args)

        def assertion_callback(env):
            self.assertEqual(env.ctx, self.env.get_context())
            self.assertEqual(env.supported_utilities, SupportedToolingsCli)
            Assertion.expect_equal_objects(
                self,
                env.args,
                UtilityInstallerRunnerCmdArgs(
                    utilities=fake_cmd_args.utils_to_install,
                    sub_command_name=InstallerSubCommandName.CLI,
                    dynamic_args=DynamicArgs(DYNAMIC_ARGS_DICT),
                    remote_opts=fake_cmd_args.remote_opts,
                    git_access_token=fake_cmd_args.git_access_token,
                ),
            )

        Assertion.expect_call_arguments(self, run_call, arg_name="env", assertion_callable=assertion_callback)
