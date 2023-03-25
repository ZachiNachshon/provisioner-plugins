#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_features_lib.remote.typer_remote_opts_fakes import TestDataRemoteOpts
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv

from provisioner_installers_plugin.installer.cmd.installer_cmd import (
    ProvisionerRunAnsiblePlaybookRelativePathFromRoot,
    UtilityInstallerCmd,
    UtilityInstallerCmdArgs,
)
from provisioner_installers_plugin.installer.runner.installer_runner import (
    UtilityInstallerRunnerCmdArgs,
)
from provisioner_installers_plugin.installer.utilities import SupportedToolings

UTILITY_INSTALLER_CMD_RUNNER_PATH = (
    "provisioner_installers_plugin.installer.runner.installer_runner.UtilityInstallerCmdRunner"
)

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_installers_plugin/installer/cmd/installer_cmd_test.py
#
class UtilityInstallerCmdTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_utility_installer_args(self) -> UtilityInstallerCmdArgs:
        return UtilityInstallerCmdArgs(
            utilities=["anchor", "k3s-agent"],
            github_access_token="test-github-access-token",
            remote_opts=TestDataRemoteOpts.create_fake_cli_remote_opts(),
        )

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}.run")
    def test_utility_install_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        fake_cmd_args = self.create_fake_utility_installer_args()

        UtilityInstallerCmd().run(ctx=self.env.get_context(), args=fake_cmd_args)

        def assertion_callback(env):
            self.assertEqual(env.ctx, self.env.get_context())
            self.assertEqual(env.supported_utilities, SupportedToolings)
            Assertion.expect_equal_objects(
                self,
                env.args,
                UtilityInstallerRunnerCmdArgs(
                    utilities=fake_cmd_args.utilities,
                    remote_opts=fake_cmd_args.remote_opts,
                    github_access_token=fake_cmd_args.github_access_token,
                    ansible_playbook_relative_path_from_module=ProvisionerRunAnsiblePlaybookRelativePathFromRoot,
                ),
            )

        Assertion.expect_call_arguments(self, run_call, arg_name="env", assertion_callable=assertion_callback)
