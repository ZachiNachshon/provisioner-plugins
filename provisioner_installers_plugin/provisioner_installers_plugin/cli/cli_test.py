# !/usr/bin/env python3

import unittest
from unittest import mock

import typer
from provisioner.cli.state import CliGlobalArgs
from provisioner.errors.cli_errors import (
    CliApplicationException,
)
from provisioner.infra.context import Context
from provisioner.test_lib.assertions import Assertion
from provisioner.test_lib.test_cli_runner import TestCliRunner
from provisioner.test_lib.test_env import TestEnv
from provisioner_features_lib.remote.domain.config import RemoteConfig
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts
from typer.testing import CliRunner

from provisioner_installers_plugin.cli.cli import anchor, helm, register_cli_commands
from provisioner_installers_plugin.k3s.cli import k3s_agent, k3s_server, register_k3s_commands
from provisioner_installers_plugin.main_fake import get_fake_app

INSTALLER_CMD_MODULE_PATH = "provisioner_installers_plugin.installer.cmd.installer_cmd"


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_installers_plugin/cli/cli_test.py
#
class UtilityInstallerCliTestShould(unittest.TestCase):

    env = TestEnv.create()

    @staticmethod
    def create_local_utility_installer_runner(runner: CliRunner):
        return runner.invoke(
            get_fake_app(),
            [
                "--dry-run",
                "--verbose",
                "--auto-prompt",
                "install",
                "--environment=Local",
                "cli",
                "anchor",
            ],
        )

    @staticmethod
    def create_remote_utility_installer_runner(runner: CliRunner):
        return runner.invoke(
            get_fake_app(),
            [
                "--dry-run",
                "--verbose",
                "--auto-prompt",
                "install",
                "--environment=Remote",
                "cli",
                "anchor",
            ],
        )

    @mock.patch(f"{INSTALLER_CMD_MODULE_PATH}.UtilityInstallerCmd.run")
    def test_e2e_run_all_cli_commands_success(self, run_call: mock.MagicMock) -> None:
        CliGlobalArgs.create(verbose=True, dry_run=True, auto_prompt=True, non_interactive=True, os_arch="DARWIN_ARM64")
        register_cli_commands(typer.Typer(), TyperRemoteOpts(remote_config=RemoteConfig({})))

        anchor()
        Assertion.expect_exists(self, run_call, arg_name="ctx")
        Assertion.expect_call_arguments(
            self, run_call, arg_name="args", assertion_callable=lambda args: self.assertIn("anchor", args.utilities)
        )

        helm()
        Assertion.expect_exists(self, run_call, arg_name="ctx")
        Assertion.expect_call_arguments(
            self, run_call, arg_name="args", assertion_callable=lambda args: self.assertIn("helm", args.utilities)
        )

    @mock.patch(f"{INSTALLER_CMD_MODULE_PATH}.UtilityInstallerCmd.run")
    def test_e2e_run_all_k3s_commands_success(self, run_call: mock.MagicMock) -> None:
        CliGlobalArgs.create(verbose=True, dry_run=True, auto_prompt=True, non_interactive=True, os_arch="DARWIN_ARM64")
        register_k3s_commands(typer.Typer(), TyperRemoteOpts(remote_config=RemoteConfig({})))

        k3s_server()
        Assertion.expect_exists(self, run_call, arg_name="ctx")
        Assertion.expect_call_arguments(
            self, run_call, arg_name="args", assertion_callable=lambda args: self.assertIn("k3s-server", args.utilities)
        )

        k3s_agent()
        Assertion.expect_exists(self, run_call, arg_name="ctx")
        Assertion.expect_call_arguments(
            self, run_call, arg_name="args", assertion_callable=lambda args: self.assertIn("k3s-agent", args.utilities)
        )

    @mock.patch(f"{INSTALLER_CMD_MODULE_PATH}.UtilityInstallerCmd.run")
    def test_run_utility_install_cmd_with_args_success(self, run_call: mock.MagicMock) -> None:
        TestCliRunner.run(UtilityInstallerCliTestShould.create_local_utility_installer_runner)
        Assertion.expect_exists(self, run_call, arg_name="ctx")
        Assertion.expect_exists(self, run_call, arg_name="args")

    @mock.patch(f"{INSTALLER_CMD_MODULE_PATH}.UtilityInstallerCmd.run", side_effect=Exception())
    def test_run_utility_install_cmd_unmanaged_failure(self, run_call: mock.MagicMock) -> None:
        Assertion.expect_raised_failure(
            self,
            ex_type=CliApplicationException,
            method_to_run=lambda: TestCliRunner.run(
                UtilityInstallerCliTestShould.create_local_utility_installer_runner
            ),
        )

    def test_e2e_run_local_utility_install_success(self) -> None:
        os_arch_pair = Context.create().os_arch.as_pair()
        Assertion.expect_outputs(
            self,
            expected=[
                "About to install the following CLI utilities:",
                "- anchor",
                "Running on Local environment",
                """{
  "summary": {
    "anchor": {
      "display_name": "anchor",
      "binary_name": "anchor",
      "version": "v0.12.0",
      "source": {
        "github": {
          "owner": "ZachiNachshon",
          "repo": "anchor",
          "supported_releases": [
            "darwin_amd64",
            "darwin_arm64",
            "linux_amd64",
            "linux_arm",
            "linux_arm64"
          ],
          "git_access_token": null,
          "release_name_resolver": null
        },
        "script": null,
        "ansible": null
      },
      "active_source": "GitHub"
    }
  }
}""",
                f"Downloading from GitHub. owner: ZachiNachshon, repo: anchor, name: anchor_0.12.0_{os_arch_pair}.tar.gz, version: v0.12.0",
            ],
            method_to_run=lambda: TestCliRunner.run(
                UtilityInstallerCliTestShould.create_local_utility_installer_runner
            ),
        )

    def test_e2e_run_remote_utility_install_success(self) -> None:
        Assertion.expect_outputs(
            self,
            expected=["About to install the following CLI utilities:", "- anchor", "Running on Remote environment"],
            method_to_run=lambda: TestCliRunner.run(
                UtilityInstallerCliTestShould.create_remote_utility_installer_runner
            ),
        )
