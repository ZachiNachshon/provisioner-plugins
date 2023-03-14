#!/usr/bin/env python3

import unittest
from typing import List
from unittest import mock

from provisioner_features_lib.remote.domain.config import RunEnvironment
from provisioner_features_lib.remote.typer_remote_opts_fakes import TestDataRemoteOpts
from python_core_lib.errors.cli_errors import (
    InstallerSourceNotSupported,
    InstallerUtilityNotSupported,
    MissingInstallerSource,
)
from python_core_lib.func.pyfn import Environment, PyFn, PyFnEvaluator
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv

from provisioner_installers_plugin.installer.domain.installable import Installable
from provisioner_installers_plugin.installer.domain.source import (
    ActiveInstallSource,
    InstallSources,
)
from provisioner_installers_plugin.installer.runner.installer_runner import (
    InstallerEnv,
    RunEnv_Utilities_Tuple,
    Utility_InstallStatus_Tuple,
    UtilityInstallerCmdRunner,
    UtilityInstallerRunnerCmdArgs,
)
from provisioner_installers_plugin.installer.utilities import SupportedToolings

TestSupportedToolings = {
    "test_util_1": Installable.Utility(
        display_name="test_util_1",
        binary_name="test_util_1",
        version="test_util_1-ver_1",
        active_source=ActiveInstallSource.GitHub,
        sources=InstallSources(
            github=InstallSources.GitHub(
                owner="TestOwner",
                repo="TestRepo",
                supported_releases=["darwin_amd64", "darwin_arm64", "linux_amd64", "linux_arm", "linux_arm64"],
                release_name_resolver=lambda version, os, arch: f"test_util_1_{os}_{arch}.tar.gz",
            ),
        ),
    ),
    "test_util_2": Installable.Utility(
        display_name="test_util_2",
        binary_name="test_util_2",
        version="test_util_2-ver_2",
        active_source=ActiveInstallSource.Script,
        sources=InstallSources(
            script=InstallSources.Script(install_cmd="curl -sfL https://my.test.install.domain.io | sh - "),
        ),
    ),
    "test_util_no_source": Installable.Utility(
        display_name="test_util_no_source",
        binary_name="test_util_no_source",
        version="test_util_no_source-ver_none",
        active_source=None,
        sources=InstallSources(),
    ),
    "test_util_no_version": Installable.Utility(
        display_name="test_util_no_source",
        binary_name="test_util_no_source",
        version=None,
        active_source=None,
        sources=InstallSources(),
    ),
}


FAKE_UTILITIES_TO_INSTALL = [
    TestSupportedToolings["test_util_1"],
    TestSupportedToolings["test_util_2"],
    TestSupportedToolings["test_util_no_source"],
]
TEST_GITHUB_ACCESS_TOKEN = "top-secret"

UTILITY_INSTALLER_CMD_RUNNER_PATH = (
    "provisioner_installers_plugin.installer.runner.installer_runner.UtilityInstallerCmdRunner"
)

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_installers_plugin/installer/runner/installer_runner_test.py
#
class UtilityInstallerRunnerTestShould(unittest.TestCase):

    env = TestEnv.create(verbose=True)

    def create_fake_installer_env(
        self,
        test_env: TestEnv,
        utilities: List[str] = ["test_util_1", "test_util_2"],
        environment: RunEnvironment = RunEnvironment.Local,
    ) -> InstallerEnv:
        return InstallerEnv(
            ctx=test_env.get_context(),
            collaborators=test_env.get_collaborators(),
            args=UtilityInstallerRunnerCmdArgs(
                utilities=utilities,
                remote_opts=TestDataRemoteOpts.create_fake_cli_remote_opts(environment),
                github_access_token=TEST_GITHUB_ACCESS_TOKEN,
            ),
            supported_utilities=TestSupportedToolings,
        )

    def create_evaluator(self, installer_env: InstallerEnv) -> "PyFnEvaluator[InstallerEnv, None]":
        return PyFnEvaluator[UtilityInstallerCmdRunner, Exception].new(UtilityInstallerCmdRunner(ctx=installer_env.ctx))

    def get_runner(self, eval: "PyFnEvaluator[InstallerEnv, None]") -> UtilityInstallerCmdRunner:
        return eval << Environment[UtilityInstallerCmdRunner]()

    def test_verify_selected_utilities_return_no_error(self) -> None:
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._verify_selected_utilities(fake_installer_env)
        self.assertIsNone(result)

    def test_verify_selected_utilities_fails_unsupported_utility(self) -> None:
        fake_installer_env = self.create_fake_installer_env(self.env, utilities=["utility-not-supported"])
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_raised_failure(
            self,
            ex_type=InstallerUtilityNotSupported,
            method_to_run=lambda: eval << self.get_runner(eval)._verify_selected_utilities(fake_installer_env),
        )

    def test_map_to_utilities_list_success(self) -> None:
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._map_to_utilities_list(fake_installer_env)
        self.assertEqual(2, len(result))
        test_env.get_collaborators().summary().assert_value(
            attribute_name="utilities",
            value=[
                fake_installer_env.supported_utilities["test_util_1"],
                fake_installer_env.supported_utilities["test_util_2"],
            ],
        )

    def test_print_installer_welcome_success(self) -> None:
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._print_installer_welcome(fake_installer_env, FAKE_UTILITIES_TO_INSTALL)
        self.assertEqual(len(FAKE_UTILITIES_TO_INSTALL), len(result))
        test_env.get_collaborators().printer().assert_outputs(
            [
                f"- {FAKE_UTILITIES_TO_INSTALL[0].display_name}",
                f"- {FAKE_UTILITIES_TO_INSTALL[1].display_name}",
                f"- {FAKE_UTILITIES_TO_INSTALL[2].display_name}",
                "Running on [yellow]Local[/yellow] environment.",
            ]
        )

    def test_resolve_run_environment_with_run_env(self) -> None:
        fake_installer_env = self.create_fake_installer_env(self.env, environment=RunEnvironment.Local)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_equal_objects(
            self,
            obj1=eval << self.get_runner(eval)._resolve_run_environment(fake_installer_env, FAKE_UTILITIES_TO_INSTALL),
            obj2=RunEnv_Utilities_Tuple(RunEnvironment.Local, FAKE_UTILITIES_TO_INSTALL),
        )

    def test_resolve_run_environment_without_run_env(self) -> None:
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env, environment=None)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_equal_objects(
            self,
            obj1=eval << self.get_runner(eval)._resolve_run_environment(fake_installer_env, FAKE_UTILITIES_TO_INSTALL),
            obj2=RunEnv_Utilities_Tuple(RunEnvironment.Local, FAKE_UTILITIES_TO_INSTALL),
        )
        test_env.get_collaborators().prompter().assert_user_single_selection_prompt("Please choose an environment")
        test_env.get_collaborators().summary().assert_value("run_env", RunEnvironment.Local)

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._run_local_utilities_installation")
    def test_run_installation_on_local_env(self, run_call: mock.MagicMock) -> None:
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._run_installation(
            fake_installer_env, RunEnv_Utilities_Tuple(RunEnvironment.Local, FAKE_UTILITIES_TO_INSTALL)
        )
        Assertion.expect_call_argument(self, run_call, "env", fake_installer_env)
        Assertion.expect_call_argument(self, run_call, "utilities", FAKE_UTILITIES_TO_INSTALL)

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._run_remote_installation")
    def test_run_installation_on_remote_env(self, run_call: mock.MagicMock) -> None:
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._run_installation(
            fake_installer_env, RunEnv_Utilities_Tuple(RunEnvironment.Remote, FAKE_UTILITIES_TO_INSTALL)
        )
        Assertion.expect_call_argument(self, run_call, "env", fake_installer_env)
        Assertion.expect_call_argument(self, run_call, "utilities", FAKE_UTILITIES_TO_INSTALL)

    def test_install_utility_skips_on_missing_utility(self) -> None:
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._install_utility(fake_installer_env, maybe_utility=None)
        self.assertIsNone(result)

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_utility_locally")
    def test_install_utility_success(self, run_call: mock.MagicMock) -> None:
        test_env = TestEnv.create()
        utility_to_install = FAKE_UTILITIES_TO_INSTALL[0]
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._install_utility(fake_installer_env, maybe_utility=utility_to_install)
        Assertion.expect_exists(self, run_call, "env")
        Assertion.expect_call_argument(self, run_call, "utility", utility_to_install)
        test_env.get_collaborators().summary().assert_show_summay_title(
            f"Installing Utility: {utility_to_install.display_name}"
        )

    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_utility",
        side_effect=[PyFn.of(FAKE_UTILITIES_TO_INSTALL[0]), PyFn.of(FAKE_UTILITIES_TO_INSTALL[1])],
    )
    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._notify_if_utility_already_installed",
        side_effect=[
            PyFn.of(FAKE_UTILITIES_TO_INSTALL[0]),
            PyFn.of(FAKE_UTILITIES_TO_INSTALL[1]),
        ],
    )
    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._check_if_utility_already_installed",
        side_effect=[
            PyFn.of(Utility_InstallStatus_Tuple(FAKE_UTILITIES_TO_INSTALL[0], True)),
            PyFn.of(Utility_InstallStatus_Tuple(FAKE_UTILITIES_TO_INSTALL[1], False)),
        ],
    )
    def test_run_local_utilities_installation_chain_success(
        self, check_call: mock.MagicMock, notify_call: mock.MagicMock, install_call: mock.MagicMock
    ) -> None:
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._run_local_utilities_installation(fake_installer_env, FAKE_UTILITIES_TO_INSTALL)
        self.assertEqual(len(FAKE_UTILITIES_TO_INSTALL), check_call.call_count)
        check_call.assert_has_calls(
            any_order=False,
            calls=[
                mock.call(fake_installer_env, FAKE_UTILITIES_TO_INSTALL[0]),
                mock.call(fake_installer_env, FAKE_UTILITIES_TO_INSTALL[1]),
            ],
        )
        self.assertEqual(2, notify_call.call_count)
        notify_call.assert_has_calls(
            any_order=False,
            calls=[
                mock.call(fake_installer_env, FAKE_UTILITIES_TO_INSTALL[0], True),
                mock.call(fake_installer_env, FAKE_UTILITIES_TO_INSTALL[1], False),
            ],
        )
        self.assertEqual(2, install_call.call_count)
        install_call.assert_has_calls(
            any_order=False,
            calls=[
                mock.call(fake_installer_env, FAKE_UTILITIES_TO_INSTALL[0]),
                mock.call(fake_installer_env, FAKE_UTILITIES_TO_INSTALL[1]),
            ],
        )

    def test_check_if_utility_already_installed(self) -> None:
        tool_binary_name = FAKE_UTILITIES_TO_INSTALL[0].binary_name
        test_env = TestEnv.create()
        test_env.get_collaborators().checks().mock_utility(tool_binary_name, exist=True)
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._check_if_utility_already_installed(
            fake_installer_env, FAKE_UTILITIES_TO_INSTALL[0]
        )
        Assertion.expect_equal_objects(
            self, result, Utility_InstallStatus_Tuple(utility=FAKE_UTILITIES_TO_INSTALL[0], installed=True)
        )
        test_env.get_collaborators().checks().assert_is_tool_exist(name=tool_binary_name, exist=True)

    def test_notify_if_utility_already_installed(self) -> None:
        tool_binary_name = FAKE_UTILITIES_TO_INSTALL[0].binary_name
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._notify_if_utility_already_installed(
            fake_installer_env, FAKE_UTILITIES_TO_INSTALL[0], exists=True
        )
        self.assertIsNone(result)
        test_env.get_collaborators().printer().assert_output(
            message=f"Utility already installed locally. name: {tool_binary_name}"
        )

    def test_do_not_notify_if_utility_not_installed(self) -> None:
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._notify_if_utility_already_installed(
            fake_installer_env, FAKE_UTILITIES_TO_INSTALL[0], exists=False
        )
        Assertion.expect_equal_objects(self, result, FAKE_UTILITIES_TO_INSTALL[0])

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_from_github")
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_from_script")
    def test_install_utility_locally_from_source_script(
        self, script_source_call: mock.MagicMock, github_source_call: mock.MagicMock
    ) -> None:
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._install_utility_locally(fake_installer_env, FAKE_UTILITIES_TO_INSTALL[1])
        self.assertEqual(0, github_source_call.call_count)
        self.assertEqual(1, script_source_call.call_count)
        script_source_call.assert_has_calls(
            any_order=False, calls=[mock.call(fake_installer_env, FAKE_UTILITIES_TO_INSTALL[1])]
        )

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_from_github")
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_from_script")
    def test_install_utility_locally_from_source_github(
        self, script_source_call: mock.MagicMock, github_source_call: mock.MagicMock
    ) -> None:
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._install_utility_locally(fake_installer_env, FAKE_UTILITIES_TO_INSTALL[0])
        self.assertEqual(0, script_source_call.call_count)
        self.assertEqual(1, github_source_call.call_count)
        github_source_call.assert_has_calls(
            any_order=False, calls=[mock.call(fake_installer_env, FAKE_UTILITIES_TO_INSTALL[0])]
        )

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_from_github")
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_from_script")
    def test_fail_to_install_utility_locally_due_to_missing_source(
        self, script_source_call: mock.MagicMock, github_source_call: mock.MagicMock
    ) -> None:
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_raised_failure(
            self,
            ex_type=InstallerSourceNotSupported,
            method_to_run=lambda: eval
            << self.get_runner(eval)._install_utility_locally(fake_installer_env, FAKE_UTILITIES_TO_INSTALL[2]),
        )
        self.assertEqual(0, script_source_call.call_count)
        self.assertEqual(0, github_source_call.call_count)

    def test_install_from_script_success(self) -> None:
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_raised_failure(
            self,
            ex_type=MissingInstallerSource,
            method_to_run=lambda: eval
            << self.get_runner(eval)._install_from_script(fake_installer_env, FAKE_UTILITIES_TO_INSTALL[2]),
        )

    def test_install_from_script_failure(self) -> None:
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._install_from_script(fake_installer_env, FAKE_UTILITIES_TO_INSTALL[1])
        test_env.get_collaborators().process().assert_run_command(
            args=[FAKE_UTILITIES_TO_INSTALL[1].sources.script.install_cmd]
        )
        Assertion.expect_equal_objects(self, result, FAKE_UTILITIES_TO_INSTALL[1])

    def test_resolve_utility_version_when_version_is_defined(self) -> None:
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._try_resolve_utility_version(
            fake_installer_env, FAKE_UTILITIES_TO_INSTALL[1]
        )
        test_env.get_collaborators().process().assert_run_command(
            args=[FAKE_UTILITIES_TO_INSTALL[1].sources.script.install_cmd]
        )
        Assertion.expect_equal_objects(self, result, FAKE_UTILITIES_TO_INSTALL[1])

    def test_resolve_utility_version_when_version_is_missing(self) -> None:
        pass
