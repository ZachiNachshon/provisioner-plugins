# !/usr/bin/env python3

import unittest
from unittest import mock

from python_core_lib.cli.state import CliGlobalArgs
from python_core_lib.errors.cli_errors import (
    CliApplicationException,
    StepEvaluationFailure,
)
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_cli_runner import TestCliRunner
from python_core_lib.test_lib.test_env import TestEnv
from typer.testing import CliRunner

from provisioner_installers_plugin.cli.anchor.cli import anchor
from provisioner_installers_plugin.cli.helm.cli import helm
from provisioner_installers_plugin.cli.k3s.cli import k3s_agent, k3s_server
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
                "cli",
                "--environment=Local",
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
                "cli",
                "--environment=Remote",
                "anchor",
            ],
        )

    @mock.patch(f"{INSTALLER_CMD_MODULE_PATH}.UtilityInstallerCmd.run")
    def test_e2e_run_local_utility_install_all_utilities_success(self, run_call: mock.MagicMock) -> None:
        CliGlobalArgs.create(verbose=True, dry_run=True, auto_prompt=True, os_arch="DARWIN_ARM64")
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

    @mock.patch(f"{INSTALLER_CMD_MODULE_PATH}.UtilityInstallerCmd.run", side_effect=StepEvaluationFailure())
    def test_run_utility_install_cmd_managed_failure(self, run_call: mock.MagicMock) -> None:
        Assertion.expect_output(
            self,
            expected="StepEvaluationFailure",
            method_to_run=lambda: TestCliRunner.run(
                UtilityInstallerCliTestShould.create_local_utility_installer_runner
            ),
        )

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
        Assertion.expect_outputs(
            self,
            expected=[
                "About to install the following CLI utilities:",
                "- anchor",
                "Running on Local environment",
                """{
  "summary": {
    "utilities": [
      {
        "display_name": "anchor",
        "binary_name": "anchor",
        "version": "v0.10.0",
        "sources": {
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
            "github_access_token": null,
            "release_name_resolver": {}
          },
          "script": null
        },
        "active_source": "GitHub"
      }
    ]
  }
}""",
                "Downloading from GitHub. owner: ZachiNachshon, repo: anchor, name: anchor_0.10.0_darwin_arm64.tar.gz, version: v0.10.0",
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
