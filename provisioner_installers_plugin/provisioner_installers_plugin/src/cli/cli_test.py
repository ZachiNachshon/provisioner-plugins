# !/usr/bin/env python3

import unittest
from unittest import mock

import click
from provisioner_installers_plugin.main_fake import get_fake_app
from provisioner_installers_plugin.src.cli.cli import register_cli_commands
from provisioner_installers_plugin.src.k3s.cli import register_k3s_commands

from plugins.provisioner_installers_plugin.provisioner_installers_plugin.src.config.domain.config_fakes import (
    TestDataInstallersConfig,
)
from plugins.provisioner_installers_plugin.provisioner_installers_plugin.src.installer.domain.command import (
    InstallerSubCommandName,
)
from provisioner_shared.components.runtime.errors.cli_errors import CliApplicationException
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.test_lib.assertions import Assertion
from provisioner_shared.components.runtime.test_lib.test_cli_runner import TestCliRunner
from provisioner_shared.components.runtime.test_lib.test_env import TestEnv

INSTALLER_CMD_MODULE_PATH = "provisioner_installers_plugin.src.installer.cmd.installer_cmd"


# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_installers_plugin/provisioner_installers_plugin/src/cli/cli_test.py
#
class UtilityInstallerCliTestShould(unittest.TestCase):

    env = TestEnv.create()

    @staticmethod
    def create_cli_installer_runner(cli_app: click.Group, utility_name: str, is_remote: bool = False):
        os_arch_pair = Context.create().os_arch.as_pair(mapping={"x86_64": "amd64"})
        args = [
            "--dry-run",
            "--verbose",
            "--auto-prompt",
            "--non-interactive",
            "--os-arch",
            os_arch_pair,
            "install",
            "cli",
        ]
        if is_remote:
            args.append("--environment=Remote")
        args.append(utility_name)
        return TestCliRunner.run(cli_app, args)

    @staticmethod
    def create_k3s_installer_runner(cli_app: click.Group, utility_name: str, is_remote: bool = False):
        os_arch_pair = Context.create().os_arch.as_pair(mapping={"x86_64": "amd64"})
        return TestCliRunner.run(
            cli_app,
            [
                "--dry-run",
                "--verbose",
                "--auto-prompt",
                "--non-interactive",
                "--os-arch",
                os_arch_pair,
                "install",
                # "--environment=Remote" if is_remote else "",
                "k3s",
                utility_name,
            ],
        )

    def assert_cli(self, fake_app: click.Group, run_call: mock.MagicMock, utility_name: str):
        def assert_cli_call(self, name: str):
            def assertion_callback(args):
                self.assertIn(name, args.utilities)
                self.assertEqual(InstallerSubCommandName.CLI, args.sub_command_name)
                self.assertIsNotNone(args.remote_opts)

            return assertion_callback

        self.create_cli_installer_runner(fake_app, utility_name=utility_name)
        Assertion.expect_exists(self, run_call, arg_name="ctx")
        Assertion.expect_call_arguments(
            self, run_call, arg_name="args", assertion_callable=assert_cli_call(self, utility_name)
        )

    def assert_k3s(self, fake_app: click.Group, run_call: mock.MagicMock, utility_name: str):
        def assert_cli_call(self, name: str):
            def assertion_callback(args):
                self.assertIn(name, args.utilities)
                self.assertEqual(InstallerSubCommandName.K3S, args.sub_command_name)
                self.assertIsNotNone(args.remote_opts)

            return assertion_callback

        self.create_k3s_installer_runner(fake_app, utility_name=utility_name)
        Assertion.expect_exists(self, run_call, arg_name="ctx")
        Assertion.expect_call_arguments(
            self, run_call, arg_name="args", assertion_callable=assert_cli_call(self, utility_name)
        )

    @mock.patch(f"{INSTALLER_CMD_MODULE_PATH}.UtilityInstallerCmd.run")
    def test_run_all_cli_commands_success(self, run_call: mock.MagicMock) -> None:
        fake_app = get_fake_app()
        fake_cfg = TestDataInstallersConfig.create_fake_installers_config()
        register_cli_commands(cli_group=fake_app, installers_cfg=fake_cfg)

        self.assert_cli(fake_app, run_call, "anchor")
        self.assert_cli(fake_app, run_call, "helm")

    @mock.patch(f"{INSTALLER_CMD_MODULE_PATH}.UtilityInstallerCmd.run")
    def test_run_all_k3s_commands_success(self, run_call: mock.MagicMock) -> None:
        fake_app = get_fake_app()
        fake_cfg = TestDataInstallersConfig.create_fake_installers_config()
        register_k3s_commands(cli_group=fake_app, installers_cfg=fake_cfg)

        self.assert_k3s(fake_app, run_call, "k3s-server")
        self.assert_k3s(fake_app, run_call, "k3s-agent")

    @mock.patch(f"{INSTALLER_CMD_MODULE_PATH}.UtilityInstallerCmd.run", side_effect=Exception())
    def test_run_utility_install_cmd_unmanaged_failure_on_verbose_only(self, run_call: mock.MagicMock) -> None:
        Assertion.expect_raised_failure(
            self,
            ex_type=CliApplicationException,
            method_to_run=lambda: TestCliRunner.run_raw(
                get_fake_app(),
                [
                    "install",
                    "cli",
                    "helm",
                    "--verbose",
                ],
            ),
        )

    def test_expect_detailed_local_install_summary_when_using_verbose(self) -> None:
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
            method_to_run=lambda: self.create_cli_installer_runner(get_fake_app(), "anchor"),
        )

    def test_run_remote_utility_install_success(self) -> None:
        Assertion.expect_outputs(
            self,
            expected=["About to install the following CLI utilities:", "- anchor", "Running on Remote environment"],
            method_to_run=lambda: self.create_cli_installer_runner(get_fake_app(), "anchor", is_remote=True),
        )
