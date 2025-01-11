#!/usr/bin/env python3

import unittest
from typing import Callable, List
from unittest import mock

from provisioner_installers_plugin.src.installer.domain.command import InstallerSubCommandName
from provisioner_installers_plugin.src.installer.domain.installable import Installable
from provisioner_installers_plugin.src.installer.domain.source import (
    ActiveInstallSource,
    InstallSource,
)
from provisioner_installers_plugin.src.installer.runner.installer_runner import (
    ANSIBLE_PLAYBOOK_REMOTE_PROVISIONER_WRAPPER,
    InstallerEnv,
    ProvisionerInstallableBinariesPath,
    ProvisionerInstallableSymlinksPath,
    ReleaseFilename_ReleaseDownloadFilePath_Utility_Tuple,
    RunEnv_Utilities_Tuple,
    SSHConnInfo_Utility_Tuple,
    UnpackedReleaseFolderPath_Utility_Tuple,
    Utility_InstallStatus_Tuple,
    Utility_Version_ReleaseFileName_Tuple,
    Utility_Version_Tuple,
    UtilityInstallerCmdRunner,
    UtilityInstallerRunnerCmdArgs,
    generate_installer_welcome,
)

from provisioner_shared.components.remote.domain.config import RunEnvironment
from provisioner_shared.components.remote.remote_connector import RemoteMachineConnector
from provisioner_shared.components.remote.remote_connector_fakes import (
    TestDataRemoteConnector,
)
from components.remote.remote_opts_fakes import TestDataRemoteOpts
from provisioner_shared.components.runtime.errors.cli_errors import (
    InstallerSourceError,
    InstallerUtilityNotSupported,
    OsArchNotSupported,
    VersionResolverError,
)
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.infra.remote_context import RemoteContext
from provisioner_shared.components.runtime.runner.ansible.ansible_fakes import FakeAnsibleRunnerLocal
from provisioner_shared.components.runtime.runner.ansible.ansible_runner import AnsiblePlaybook
from provisioner_shared.components.runtime.test_lib import faker
from provisioner_shared.components.runtime.test_lib.assertions import Assertion
from provisioner_shared.components.runtime.test_lib.test_env import TestEnv
from provisioner_shared.components.runtime.utils.os import OsArch
from provisioner_shared.components.runtime.utils.summary import Summary
from provisioner_shared.framework.functional.pyfn import Environment, PyFn, PyFnEvaluator

# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_installers_plugin/src/installer/runner/installer_runner_test.py
#
TEST_GITHUB_ACCESS_TOKEN = "top-secret"
TEST_UTILITY_1_NAME_GITHUB = "test_util_github"
TEST_UTILITY_2_NAME_SCRIPT = "test_util_script"

UTILITY_INSTALLER_CMD_RUNNER_PATH = (
    "provisioner_installers_plugin.src.installer.runner.installer_runner.UtilityInstallerCmdRunner"
)
REMOTE_MACHINE_CONNECTOR_PATH = "provisioner_shared.components.remote.remote_connector.RemoteMachineConnector"

TestSupportedToolings = {
    TEST_UTILITY_1_NAME_GITHUB: Installable.Utility(
        display_name=TEST_UTILITY_1_NAME_GITHUB,
        binary_name=TEST_UTILITY_1_NAME_GITHUB,
        version="test_util_github-ver_1",
        active_source=ActiveInstallSource.GitHub,
        sources=InstallSource(
            github=InstallSource.GitHub(
                owner="TestOwner",
                repo="TestRepo",
                supported_releases=[
                    "darwin_test_arch",
                    "darwin_amd64",
                    "darwin_arm64",
                    "linux_amd64",
                    "linux_arm",
                    "linux_arm64",
                ],
                release_name_resolver=lambda version, os, arch: f"test_util_github_{version}_{os}_{arch}.tar.gz",
            ),
        ),
    ),
    TEST_UTILITY_2_NAME_SCRIPT: Installable.Utility(
        display_name=TEST_UTILITY_2_NAME_SCRIPT,
        binary_name=TEST_UTILITY_2_NAME_SCRIPT,
        version="test_util_script-ver_2",
        active_source=ActiveInstallSource.Script,
        sources=InstallSource(
            script=InstallSource.Script(install_cmd="curl -sfL https://my.test.install.domain.io | sh - "),
        ),
    ),
    "test_util_no_source": Installable.Utility(
        display_name="test_util_no_source",
        binary_name="test_util_no_source",
        version="test_util_no_source-ver_none",
        active_source=None,
        sources=InstallSource(),
    ),
    "test_util_no_version_no_source": Installable.Utility(
        display_name="test_util_no_version_no_source",
        binary_name="test_util_no_version_no_source",
        version=None,
        active_source=None,
        sources=InstallSource(),
    ),
    "test_util_github_no_version": Installable.Utility(
        display_name="test_util_github",
        binary_name="test_util_github",
        version=None,
        active_source=ActiveInstallSource.GitHub,
        sources=InstallSource(
            github=InstallSource.GitHub(
                owner="TestOwner",
                repo="TestRepo",
                supported_releases=[
                    "darwin_test_arch",
                    "darwin_amd64",
                    "darwin_arm64",
                    "linux_amd64",
                    "linux_arm",
                    "linux_arm64",
                ],
                release_name_resolver=lambda version, os, arch: f"test_util_github_{version}_{os}_{arch}.tar.gz",
            ),
        ),
    ),
}


class UtilityInstallerRunnerTestShould(unittest.TestCase):

    env = TestEnv.create(verbose=True)

    def create_fake_installer_env(
        self,
        test_env: TestEnv,
        utilities: List[str] = [TEST_UTILITY_1_NAME_GITHUB, TEST_UTILITY_2_NAME_SCRIPT],
        environment: RunEnvironment = RunEnvironment.Local,
        remote_context: RemoteContext = RemoteContext.no_op(),
    ) -> InstallerEnv:
        return InstallerEnv(
            ctx=test_env.get_context(),
            collaborators=test_env.get_collaborators(),
            args=UtilityInstallerRunnerCmdArgs(
                utilities=utilities,
                sub_command_name=InstallerSubCommandName.CLI,
                remote_opts=TestDataRemoteOpts.create_fake_cli_remote_opts(remote_context, environment),
                git_access_token=TEST_GITHUB_ACCESS_TOKEN,
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

    def test_create_utils_summary_success(self) -> None:
        utilities = [
            TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB],
            TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT],
        ]
        test_env = TestEnv.create(verbose=True)
        test_env.get_collaborators().summary().on("append", str, Installable.Utility).side_effect = (
            lambda attribute_name, value: (self.assertIn(attribute_name, utilities[0].display_name),)
        )
        test_env.get_collaborators().summary().on("append", str, Installable.Utility).side_effect = (
            lambda attribute_name, value: (self.assertIn(attribute_name, utilities[1].display_name),)
        )
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._create_utils_summary(fake_installer_env, utilities)
        self.assertEqual(2, len(result))

    def test_print_installer_welcome_success(self) -> None:
        utilities = [
            TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB],
            TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT],
        ]
        test_env = TestEnv.create()
        test_env.get_collaborators().printer().on("print_with_rich_table_fn", str, str).side_effect = (
            lambda message, border_color: (
                self.assertIn(f"- {utilities[0].display_name}", message),
                self.assertIn(f"- {utilities[1].display_name}", message),
                self.assertIn("Running on [yellow]Local[/yellow] environment.", message),
            )
        )
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._print_installer_welcome(fake_installer_env, utilities)
        self.assertEqual(len(utilities), len(result))

    def test_resolve_run_environment_with_run_env(self) -> None:
        utilities = [
            TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB],
            TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT],
        ]
        fake_installer_env = self.create_fake_installer_env(self.env, environment=RunEnvironment.Local)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_equal_objects(
            self,
            obj1=eval << self.get_runner(eval)._resolve_run_environment(fake_installer_env, utilities),
            obj2=RunEnv_Utilities_Tuple(RunEnvironment.Local, utilities),
        )

    def test_resolve_run_environment_using_user_prompt(self) -> None:
        utilities = [
            TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB],
            TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT],
        ]
        test_env = TestEnv.create()
        test_env.get_collaborators().override_summary(
            # User the real summary object to capture the value
            Summary(test_env.get_context().is_dry_run(), test_env.get_context().is_verbose(), False, None, None, None)
        )

        def on_show_summary_and_prompt_for_enter(message: str, options: List[str]) -> None:
            self.assertEqual("Please choose an environment", message)
            self.assertEqual(["Local", "Remote"], options)
            return RunEnvironment.Local

        test_env.get_collaborators().prompter().on(
            "prompt_user_single_selection_fn", str, List
        ).side_effect = on_show_summary_and_prompt_for_enter

        fake_installer_env = self.create_fake_installer_env(test_env, environment=None)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_equal_objects(
            self,
            obj1=eval << self.get_runner(eval)._resolve_run_environment(fake_installer_env, utilities),
            obj2=RunEnv_Utilities_Tuple(RunEnvironment.Local, utilities),
        )

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._run_local_utilities_installation")
    def test_run_installation_on_local_env(self, run_call: mock.MagicMock) -> None:
        utilities = [
            TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB],
            TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT],
        ]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._run_installation(
            fake_installer_env, RunEnv_Utilities_Tuple(RunEnvironment.Local, utilities)
        )
        Assertion.expect_call_argument(self, run_call, "env", fake_installer_env)
        Assertion.expect_call_argument(self, run_call, "utilities", utilities)

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._run_remote_installation")
    def test_run_installation_on_remote_env(self, run_call: mock.MagicMock) -> None:
        utilities = [
            TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB],
            TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT],
        ]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._run_installation(
            fake_installer_env, RunEnv_Utilities_Tuple(RunEnvironment.Remote, utilities)
        )
        Assertion.expect_call_argument(self, run_call, "env", fake_installer_env)
        Assertion.expect_call_argument(self, run_call, "utilities", utilities)

    def test_print_pre_install_summary_skips_on_missing_utility(self) -> None:
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._print_pre_install_summary(fake_installer_env, maybe_utility=None)
        self.assertIsNone(result)

    def test_print_pre_install_summary_success(self) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        test_env = TestEnv.create()
        test_env.get_collaborators().summary().on("show_summary_and_prompt_for_enter", str).side_effect = (
            lambda title: self.assertIn(title, f"Installing Utility: {utility.display_name}")
        )
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._print_pre_install_summary(fake_installer_env, maybe_utility=utility)

    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._print_post_install_summary",
        side_effect=[
            PyFn.of(TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]),
            PyFn.of(TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT]),
        ],
    )
    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_utility_locally",
        side_effect=[
            PyFn.of(TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]),
            PyFn.of(TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT]),
        ],
    )
    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._print_pre_install_summary",
        side_effect=[
            PyFn.of(TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]),
            PyFn.of(TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT]),
        ],
    )
    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._notify_if_utility_already_installed",
        side_effect=[
            PyFn.of(TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]),
            PyFn.of(TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT]),
        ],
    )
    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._check_if_utility_already_installed",
        side_effect=[
            PyFn.of(Utility_InstallStatus_Tuple(TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB], True)),
            PyFn.of(Utility_InstallStatus_Tuple(TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT], False)),
        ],
    )
    def test_run_local_utilities_installation_call_chain_success(
        self,
        check_call: mock.MagicMock,
        notify_call: mock.MagicMock,
        pre_print_call: mock.MagicMock,
        install_call: mock.MagicMock,
        post_print_call: mock.MagicMock,
    ) -> None:
        utility_github = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        utility_script = TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._run_local_utilities_installation(
            fake_installer_env, [utility_github, utility_script]
        )
        self.assertEqual(2, check_call.call_count)
        check_call.assert_has_calls(
            any_order=False,
            calls=[
                mock.call(fake_installer_env, utility_github),
                mock.call(fake_installer_env, utility_script),
            ],
        )
        self.assertEqual(2, notify_call.call_count)
        notify_call.assert_has_calls(
            any_order=False,
            calls=[
                mock.call(fake_installer_env, utility_github, True),
                mock.call(fake_installer_env, utility_script, False),
            ],
        )
        self.assertEqual(2, pre_print_call.call_count)
        pre_print_call.assert_has_calls(
            any_order=False,
            calls=[
                mock.call(fake_installer_env, utility_github),
                mock.call(fake_installer_env, utility_script),
            ],
        )
        self.assertEqual(2, install_call.call_count)
        install_call.assert_has_calls(
            any_order=False,
            calls=[
                mock.call(fake_installer_env, utility_github),
                mock.call(fake_installer_env, utility_script),
            ],
        )
        self.assertEqual(2, post_print_call.call_count)
        post_print_call.assert_has_calls(
            any_order=False,
            calls=[
                mock.call(fake_installer_env, utility_github),
                mock.call(fake_installer_env, utility_script),
            ],
        )

    def test_check_if_utility_already_installed(self) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        test_env = TestEnv.create()
        test_env.get_collaborators().checks().on("is_tool_exist_fn", str).return_value = True
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._check_if_utility_already_installed(fake_installer_env, utility)
        Assertion.expect_equal_objects(self, result, Utility_InstallStatus_Tuple(utility=utility, installed=True))

    def test_notify_if_utility_already_installed(self) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        test_env = TestEnv.create()
        test_env.get_collaborators().printer().on("print_fn", str).side_effect = lambda message: self.assertIn(
            message, f"Utility already installed locally. name: {utility.binary_name}"
        )
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._notify_if_utility_already_installed(
            fake_installer_env, utility, exists=True
        )
        self.assertIsNone(result)

    def test_do_not_notify_if_utility_not_installed(self) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._notify_if_utility_already_installed(
            fake_installer_env, utility, exists=False
        )
        Assertion.expect_equal_objects(self, result, utility)

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_from_github")
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_from_script")
    def test_install_utility_locally_from_source_script(
        self, script_source_call: mock.MagicMock, github_source_call: mock.MagicMock
    ) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._install_utility_locally(fake_installer_env, utility)
        self.assertEqual(0, github_source_call.call_count)
        self.assertEqual(1, script_source_call.call_count)
        script_source_call.assert_has_calls(any_order=False, calls=[mock.call(fake_installer_env, utility)])

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_from_github")
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_from_script")
    def test_install_utility_locally_from_source_github(
        self, script_source_call: mock.MagicMock, github_source_call: mock.MagicMock
    ) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._install_utility_locally(fake_installer_env, utility)
        self.assertEqual(0, script_source_call.call_count)
        self.assertEqual(1, github_source_call.call_count)
        github_source_call.assert_has_calls(any_order=False, calls=[mock.call(fake_installer_env, utility)])

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_from_github")
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_from_script")
    def test_fail_to_install_utility_locally_due_to_missing_source(
        self, script_source_call: mock.MagicMock, github_source_call: mock.MagicMock
    ) -> None:
        utility = TestSupportedToolings["test_util_no_source"]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_raised_failure(
            self,
            ex_type=InstallerSourceError,
            method_to_run=lambda: eval << self.get_runner(eval)._install_utility_locally(fake_installer_env, utility),
        )
        self.assertEqual(0, script_source_call.call_count)
        self.assertEqual(0, github_source_call.call_count)

    def test_install_from_script_failure(self) -> None:
        utility = TestSupportedToolings["test_util_no_source"]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_raised_failure(
            self,
            ex_type=InstallerSourceError,
            method_to_run=lambda: eval << self.get_runner(eval)._install_from_script(fake_installer_env, utility),
        )

    def test_install_from_script_success(self) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT]
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        test_env.get_collaborators().process().on("run_fn", List, faker.Anything, str, bool, bool).side_effect = (
            lambda args, working_dir, fail_msg, fail_on_error, allow_single_shell_command_str: self.assertEqual(
                args, [utility.source.script.install_cmd]
            )
        )
        result = eval << self.get_runner(eval)._install_from_script(fake_installer_env, utility)
        Assertion.expect_equal_objects(self, result, utility)

    def test_resolve_utility_version_when_version_is_defined(self) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._try_resolve_utility_version(fake_installer_env, utility)
        Assertion.expect_equal_objects(self, result, Utility_Version_Tuple(utility, utility.version))

    def test_resolve_utility_version_failed(self) -> None:
        utility = TestSupportedToolings["test_util_no_version_no_source"]
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_raised_failure(
            self,
            ex_type=InstallerSourceError,
            method_to_run=lambda: eval
            << self.get_runner(eval)._try_resolve_utility_version(fake_installer_env, utility),
        )

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._try_resolve_version_from_github")
    def test_resolve_utility_version_when_version_is_missing(self, run_call: mock.MagicMock) -> None:
        utility = TestSupportedToolings["test_util_github_no_version"]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._try_resolve_utility_version(fake_installer_env, utility)
        run_call.assert_called_once()
        Assertion.expect_call_argument(self, run_call, "utility", utility)

    def test_try_resolve_version_from_github_success(self) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        test_env = TestEnv.create()
        test_env.get_collaborators().github().mock_get_latest_version(
            owner=utility.source.github.owner, repo=utility.source.github.repo, version=utility.version
        )
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._try_resolve_version_from_github(fake_installer_env, utility)
        test_env.get_collaborators().github().assert_get_latest_version(
            owner=utility.source.github.owner, repo=utility.source.github.repo, version=utility.version
        )
        Assertion.expect_equal_objects(self, result, Utility_Version_Tuple(utility, utility.version))

    def test_try_resolve_version_from_github_fail(self) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        test_env = TestEnv.create()
        test_env.get_collaborators().github().mock_get_latest_version(
            owner=utility.source.github.owner, repo=utility.source.github.repo, version=None
        )
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_raised_failure(
            self,
            ex_type=VersionResolverError,
            method_to_run=lambda: eval
            << self.get_runner(eval)._try_resolve_version_from_github(fake_installer_env, utility),
        )

    def test_try_get_github_release_name_by_os_arch_success(self) -> None:
        test_env = TestEnv.create()
        utility = TestSupportedToolings["test_util_github_no_version"]
        version_from_github = "v9.9.9"
        release_filename = utility.source.github.release_name_resolver(
            version_from_github, test_env.get_context().os_arch.os, test_env.get_context().os_arch.arch
        )
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._try_get_github_release_name_by_os_arch(
            fake_installer_env, Utility_Version_Tuple(utility, version=version_from_github)
        )
        Assertion.expect_equal_objects(
            self, result, Utility_Version_ReleaseFileName_Tuple(utility, version_from_github, release_filename)
        )

    def test_try_get_github_release_name_by_os_arch_fail(self) -> None:
        test_env = TestEnv.create(ctx=Context.create(os_arch=OsArch(os="NOT_SUPPORTED")))
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_raised_failure(
            self,
            ex_type=OsArchNotSupported,
            method_to_run=lambda: eval
            << self.get_runner(eval)._try_get_github_release_name_by_os_arch(
                fake_installer_env, Utility_Version_Tuple(utility, version=None)
            ),
        )

    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._print_github_binary_info",
        return_value=Utility_Version_ReleaseFileName_Tuple(
            TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB],
            TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB].version,
            "http://download-url.com",
        ),
    )
    def test_print_before_downloading(self, run_call: mock.MagicMock) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        expected_tuple = Utility_Version_ReleaseFileName_Tuple(utility, utility.version, "http://download-url.com")
        result = eval << self.get_runner(eval)._print_before_downloading(fake_installer_env, expected_tuple)
        Assertion.expect_call_argument(self, run_call, "util_ver_name_tuple", expected_tuple)
        Assertion.expect_equal_objects(self, result, expected_tuple)

    def test_print_github_binary_info(self) -> None:
        test_env = TestEnv.create()
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        test_env.get_collaborators().printer().on("new_line_fn", int).side_effect = None
        test_env.get_collaborators().printer().on("print_fn", str).side_effect = lambda message: (
            self.assertIn(message, utility.source.github.owner),
            self.assertIn(message, utility.source.github.repo),
            self.assertIn(message, utility.version),
            self.assertIn(message, "http://download-url.com"),
        )
        fake_installer_env = self.create_fake_installer_env(test_env)
        expected_tuple = Utility_Version_ReleaseFileName_Tuple(utility, utility.version, "http://download-url.com")
        UtilityInstallerCmdRunner(test_env.get_context())._print_github_binary_info(fake_installer_env, expected_tuple)

    def test_download_binary_by_version(self) -> None:
        test_env = TestEnv.create()
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        release_filename = utility.source.github.release_name_resolver(utility.version, "test-os", "test-arch")
        dl_folderpath = f"{ProvisionerInstallableBinariesPath}/{utility.binary_name}/{utility.version}"
        dl_filepath = f"{dl_folderpath}/{release_filename}"
        expected_input = Utility_Version_ReleaseFileName_Tuple(utility, utility.version, release_filename)
        expected_output = ReleaseFilename_ReleaseDownloadFilePath_Utility_Tuple(release_filename, dl_filepath, utility)
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._download_binary_by_version(fake_installer_env, expected_input)
        Assertion.expect_equal_objects(self, result, expected_output)
        test_env.get_collaborators().github().assert_download_binary(
            utility.source.github.owner, utility.source.github.repo, utility.version, release_filename, dl_folderpath
        )

    def test_maybe_extract_downloaded_binary_success_with_archive(self) -> None:
        test_env = TestEnv.create()
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]

        unpacked_release_folderpath = f"/home/user/provisioner/binaries/{utility.binary_name}/{utility.version}"
        release_filename = utility.source.github.release_name_resolver(
            utility.version, test_env.get_context().os_arch.os, test_env.get_context().os_arch.arch
        )
        release_download_filepath = f"{unpacked_release_folderpath}/{release_filename}"

        fake_io_utils = test_env.get_collaborators().io_utils()

        def is_archive_fn(filepath: str) -> bool:
            self.assertEqual(filepath, release_download_filepath)
            return True

        fake_io_utils.on("is_archive_fn", str).side_effect = is_archive_fn

        def unpack_archive_fn(filepath: str) -> str:
            self.assertEqual(filepath, release_download_filepath)
            return unpacked_release_folderpath

        fake_io_utils.on("unpack_archive_fn", str).side_effect = unpack_archive_fn

        expected_input = ReleaseFilename_ReleaseDownloadFilePath_Utility_Tuple(
            release_filename, release_download_filepath, utility
        )
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._maybe_extract_downloaded_binary(fake_installer_env, expected_input)
        Assertion.expect_equal_objects(
            self, result, UnpackedReleaseFolderPath_Utility_Tuple(unpacked_release_folderpath, utility)
        )

    def test_maybe_extract_downloaded_binary_success_with_regular_file(self) -> None:
        test_env = TestEnv.create()
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        release_filename = utility.source.github.release_name_resolver(
            utility.version, test_env.get_context().os_arch.os, test_env.get_context().os_arch.arch
        )
        unpacked_release_folderpath = f"/home/user/provisioner/binaries/{utility.binary_name}/{utility.version}"
        release_download_filepath = f"{unpacked_release_folderpath}/{release_filename}"

        fake_io_utils = test_env.get_collaborators().io_utils()

        def is_archive_fn(filepath: str) -> bool:
            self.assertEqual(filepath, release_download_filepath)
            return False

        fake_io_utils.on("is_archive_fn", str).side_effect = is_archive_fn

        def unpack_archive_fn(filepath: str) -> str:
            self.assertEqual(filepath, release_download_filepath)
            return unpacked_release_folderpath

        fake_io_utils.on("unpack_archive_fn", str).side_effect = unpack_archive_fn

        expected_input = ReleaseFilename_ReleaseDownloadFilePath_Utility_Tuple(
            release_filename, release_download_filepath, utility
        )
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._maybe_extract_downloaded_binary(fake_installer_env, expected_input)
        Assertion.expect_equal_objects(
            self, result, UnpackedReleaseFolderPath_Utility_Tuple(unpacked_release_folderpath, utility)
        )

    def test_elevate_permission_and_symlink(self) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        unpacked_release_folderpath = f"/home/user/provisioner/binaries/{utility.binary_name}/{utility.version}"
        unpacked_release_binary_filepath = f"{unpacked_release_folderpath}/{utility.binary_name}"
        symlink_path = f"{ProvisionerInstallableSymlinksPath}/{utility.binary_name}"
        test_env = TestEnv.create()
        fake_io_utils = test_env.get_collaborators().io_utils()

        def set_file_permissions_fn(filepath: str, permissions: int) -> str:
            self.assertEqual(filepath, unpacked_release_binary_filepath)
            self.assertEqual(permissions, 0o111)
            return filepath

        fake_io_utils.on("set_file_permissions_fn", str, int).side_effect = set_file_permissions_fn

        def write_symlink_fn(source: str, target: str) -> str:
            self.assertEqual(source, unpacked_release_binary_filepath)
            self.assertEqual(target, symlink_path)
            return symlink_path

        fake_io_utils.on("write_symlink_fn", str, str).side_effect = write_symlink_fn

        expected_input = UnpackedReleaseFolderPath_Utility_Tuple(unpacked_release_folderpath, utility)
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._elevate_permission_and_symlink(fake_installer_env, expected_input)
        Assertion.expect_equal_objects(self, result, symlink_path)

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._elevate_permission_and_symlink", return_value=PyFn.empty())
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._maybe_extract_downloaded_binary", return_value=PyFn.empty())
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._download_binary_by_version", return_value=PyFn.empty())
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._print_before_downloading", return_value=PyFn.empty())
    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._try_get_github_release_name_by_os_arch", return_value=PyFn.empty()
    )
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._try_resolve_utility_version", return_value=PyFn.empty())
    def test_install_from_github_success(
        self,
        resolve_call: mock.MagicMock,
        get_release_name_call: mock.MagicMock,
        print_release_call: mock.MagicMock,
        download_binary_call: mock.MagicMock,
        extract_binary_archive_call: mock.MagicMock,
        elevate_binary_permissions_call: mock.MagicMock,
    ) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._install_from_github(fake_installer_env, utility)
        resolve_call.assert_called_once()
        get_release_name_call.assert_called_once()
        print_release_call.assert_called_once()
        download_binary_call.assert_called_once()
        extract_binary_archive_call.assert_called_once()
        elevate_binary_permissions_call.assert_called_once()

    def test_install_from_github_failed(
        self,
    ) -> None:
        utility = TestSupportedToolings["test_util_no_source"]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_raised_failure(
            self,
            ex_type=InstallerSourceError,
            method_to_run=lambda: eval << self.get_runner(eval)._install_from_github(fake_installer_env, utility),
        )

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._run_installation", return_value=PyFn.empty())
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._resolve_run_environment", return_value=PyFn.empty())
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._print_installer_welcome", return_value=PyFn.empty())
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._create_utils_summary", return_value=PyFn.empty())
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._map_to_utilities_list", return_value=PyFn.empty())
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._verify_selected_utilities", return_value=PyFn.empty())
    def test_run_success(
        self,
        verify_call: mock.MagicMock,
        map_call: mock.MagicMock,
        create_summary_call: mock.MagicMock,
        print_call: mock.MagicMock,
        resolve_call: mock.MagicMock,
        run_call: mock.MagicMock,
    ) -> None:

        fake_installer_env = self.create_fake_installer_env(self.env)
        UtilityInstallerCmdRunner.run(fake_installer_env)
        verify_call.assert_called_once()
        map_call.assert_called_once()
        create_summary_call.assert_called_once()
        print_call.assert_called_once()
        resolve_call.assert_called_once()
        run_call.assert_called_once()

    @mock.patch(
        f"{REMOTE_MACHINE_CONNECTOR_PATH}.collect_ssh_connection_info",
        return_value=TestDataRemoteConnector.create_fake_ssh_conn_info_fn()(),
    )
    def test_collect_ssh_connection_info(self, run_call: mock.MagicMock) -> None:
        test_env = TestEnv.create()
        test_env.get_collaborators().summary().on("append_result", str, Callable[[], str]).side_effect = (
            lambda attribute_name, call: (
                self.assertEqual(attribute_name, "ssh_conn_info"),
                call(),
            )
        )
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._collect_ssh_connection_info(
            fake_installer_env, RemoteMachineConnector(test_env.get_collaborators())
        )
        run_call.assert_has_calls(
            any_order=False,
            calls=[
                mock.call(fake_installer_env.ctx, fake_installer_env.args.remote_opts, force_single_conn_info=True),
            ],
        )

    def test_user_output_when_install_on_remote_machine(self) -> None:
        test_env = TestEnv.create()
        test_env.get_collaborators().progress_indicator().get_status().on(
            "long_running_process_fn", Callable, str, str
        ).side_effect = lambda call, desc_run, desc_end: (
            self.assertEqual(desc_run, "Running Ansible playbook (Provisioner Wrapper)"),
            self.assertEqual(desc_end, "Ansible playbook finished (Provisioner Wrapper)."),
        )
        fake_installer_env = self.create_fake_installer_env(test_env, remote_context=RemoteContext.create(verbose=True))
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._install_on_remote_machine(
            fake_installer_env,
            SSHConnInfo_Utility_Tuple(
                TestDataRemoteConnector.create_fake_ssh_conn_info_fn()(),
                TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB],
            ),
        )

    def test_run_ansible(self) -> None:
        utility = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        env = TestEnv.create()
        remote_ctx = RemoteContext.no_op()
        fake_runner = FakeAnsibleRunnerLocal(env.get_context())
        fake_runner.on("run_fn", List, AnsiblePlaybook, List, List, str).side_effect = (
            lambda selected_hosts, playbook, ansible_vars, ansible_tags, ansible_playbook_package: (
                self.assertEqual(selected_hosts, TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS),
                Assertion.expect_equal_objects(
                    self,
                    playbook,
                    AnsiblePlaybook(
                        name="provisioner_wrapper",
                        content=ANSIBLE_PLAYBOOK_REMOTE_PROVISIONER_WRAPPER,
                        remote_context=remote_ctx,
                    ),
                ),
                Assertion.expect_equal_objects(
                    self,
                    ansible_vars,
                    [
                        f"provisioner_command='provisioner -y {'-v ' if remote_ctx.is_verbose() else ''}install {InstallerSubCommandName.CLI} --environment=Local {utility.display_name}'",
                        "required_plugins=['provisioner_installers_plugin:0.1.0']",
                        f"git_access_token={TEST_GITHUB_ACCESS_TOKEN}",
                    ],
                ),
                self.assertEqual(ansible_tags, ["provisioner_wrapper"]),
            )
        )

        UtilityInstallerCmdRunner(env.get_context())._run_ansible(
            runner=fake_runner,
            remote_ctx=remote_ctx,
            ssh_conn_info=TestDataRemoteConnector.create_fake_ssh_conn_info_fn()(),
            sub_command_name=InstallerSubCommandName.CLI,
            utility_display_name=utility.display_name,
            git_access_token=TEST_GITHUB_ACCESS_TOKEN,
        )

    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_on_remote_machine",
        side_effect=[
            PyFn.of(f"Installed {TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB].binary_name}"),
            PyFn.of(f"Installed {TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT].binary_name}"),
        ],
    )
    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._print_pre_install_summary",
        side_effect=[
            PyFn.of(TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]),
            PyFn.of(TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT]),
        ],
    )
    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._collect_ssh_connection_info",
        return_value=PyFn.of(TestDataRemoteConnector.create_fake_ssh_conn_info_fn()()),
    )
    def test_run_remote_installation_success(
        self, collect_call: mock.MagicMock, pre_print_call: mock.MagicMock, install_call: mock.MagicMock
    ) -> None:

        utility_github = TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB]
        utility_script = TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT]
        test_env = TestEnv.create()
        test_env.get_collaborators().printer().on("new_line_fn", int).side_effect = None
        test_env.get_collaborators().printer().on("print_fn", str).side_effect = lambda message: (
            self.assertIn(message, f"Installed {TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB].binary_name}"),
        )
        test_env.get_collaborators().printer().on("new_line_fn", int).side_effect = None
        test_env.get_collaborators().printer().on("print_fn", str).side_effect = lambda message: (
            self.assertIn(message, f"Installed {TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT].binary_name}"),
        )
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._run_remote_installation(fake_installer_env, [utility_github, utility_script])
        self.assertEqual(1, collect_call.call_count)
        self.assertEqual(2, pre_print_call.call_count)
        self.assertEqual(2, install_call.call_count)

    def test_generate_installer_welcome_with_environment(self) -> None:
        utilities = [
            TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB],
            TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT],
        ]
        output = generate_installer_welcome(utilities_to_install=utilities, environment=None)
        self.assertIn("Environment was not set, you will be prompted to select a local/remote environment.", output)

    def test_generate_installer_welcome_without_environment(self) -> None:
        utilities = [
            TestSupportedToolings[TEST_UTILITY_1_NAME_GITHUB],
            TestSupportedToolings[TEST_UTILITY_2_NAME_SCRIPT],
        ]
        env_in_test = RunEnvironment.Local
        output = generate_installer_welcome(utilities_to_install=utilities, environment=env_in_test)
        self.assertIn(f"Running on [yellow]{env_in_test}[/yellow] environment.", output)
