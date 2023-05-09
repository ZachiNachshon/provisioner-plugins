#!/usr/bin/env python3

import unittest
from typing import List
from unittest import mock

from provisioner_features_lib.remote.domain.config import RunEnvironment
from provisioner_features_lib.remote.remote_connector import RemoteMachineConnector
from provisioner_features_lib.remote.remote_connector_fakes import (
    TestDataRemoteConnector,
)
from provisioner_features_lib.remote.typer_remote_opts_fakes import TestDataRemoteOpts
from python_core_lib.errors.cli_errors import (
    InstallerSourceError,
    InstallerUtilityNotSupported,
    OsArchNotSupported,
    VersionResolverError,
)
from python_core_lib.func.pyfn import Environment, PyFn, PyFnEvaluator
from python_core_lib.infra.context import Context
from python_core_lib.infra.remote_context import RemoteContext
from python_core_lib.runner.ansible.ansible_runner import AnsiblePlaybook
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv
from python_core_lib.utils.os import OsArch

from provisioner_installers_plugin.installer.domain.installable import Installable
from provisioner_installers_plugin.installer.domain.source import (
    ActiveInstallSource,
    InstallSources,
)
from provisioner_installers_plugin.installer.runner.installer_runner import (
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

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_installers_plugin/installer/runner/installer_runner_test.py
#
TEST_GITHUB_ACCESS_TOKEN = "top-secret"

UTILITY_INSTALLER_CMD_RUNNER_PATH = (
    "provisioner_installers_plugin.installer.runner.installer_runner.UtilityInstallerCmdRunner"
)
REMOTE_MACHINE_CONNECTOR_PATH = "provisioner_features_lib.remote.remote_connector.RemoteMachineConnector"

TestSupportedToolings = {
    "test_util_github": Installable.Utility(
        display_name="test_util_github",
        binary_name="test_util_github",
        version="test_util_github-ver_1",
        active_source=ActiveInstallSource.GitHub,
        sources=InstallSources(
            github=InstallSources.GitHub(
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
    "test_util_script": Installable.Utility(
        display_name="test_util_script",
        binary_name="test_util_script",
        version="test_util_script-ver_2",
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
    "test_util_no_version_no_source": Installable.Utility(
        display_name="test_util_no_version_no_source",
        binary_name="test_util_no_version_no_source",
        version=None,
        active_source=None,
        sources=InstallSources(),
    ),
    "test_util_github_no_version": Installable.Utility(
        display_name="test_util_github",
        binary_name="test_util_github",
        version=None,
        active_source=ActiveInstallSource.GitHub,
        sources=InstallSources(
            github=InstallSources.GitHub(
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
        utilities: List[str] = ["test_util_github", "test_util_script"],
        environment: RunEnvironment = RunEnvironment.Local,
        remote_context: RemoteContext = RemoteContext.no_op(),
    ) -> InstallerEnv:
        return InstallerEnv(
            ctx=test_env.get_context(),
            collaborators=test_env.get_collaborators(),
            args=UtilityInstallerRunnerCmdArgs(
                utilities=utilities,
                remote_opts=TestDataRemoteOpts.create_fake_cli_remote_opts(remote_context, environment),
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
                fake_installer_env.supported_utilities["test_util_github"],
                fake_installer_env.supported_utilities["test_util_script"],
            ],
        )

    def test_print_installer_welcome_success(self) -> None:
        utilities = [TestSupportedToolings["test_util_github"], TestSupportedToolings["test_util_script"]]
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._print_installer_welcome(fake_installer_env, utilities)
        self.assertEqual(len(utilities), len(result))
        test_env.get_collaborators().printer().assert_outputs(
            [
                f"- {utilities[0].display_name}",
                f"- {utilities[1].display_name}",
                "Running on [yellow]Local[/yellow] environment.",
            ]
        )

    def test_resolve_run_environment_with_run_env(self) -> None:
        utilities = [TestSupportedToolings["test_util_github"], TestSupportedToolings["test_util_script"]]
        fake_installer_env = self.create_fake_installer_env(self.env, environment=RunEnvironment.Local)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_equal_objects(
            self,
            obj1=eval << self.get_runner(eval)._resolve_run_environment(fake_installer_env, utilities),
            obj2=RunEnv_Utilities_Tuple(RunEnvironment.Local, utilities),
        )

    def test_resolve_run_environment_without_run_env(self) -> None:
        utilities = [TestSupportedToolings["test_util_github"], TestSupportedToolings["test_util_script"]]
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env, environment=None)
        eval = self.create_evaluator(fake_installer_env)
        Assertion.expect_equal_objects(
            self,
            obj1=eval << self.get_runner(eval)._resolve_run_environment(fake_installer_env, utilities),
            obj2=RunEnv_Utilities_Tuple(RunEnvironment.Local, utilities),
        )
        test_env.get_collaborators().prompter().assert_user_single_selection_prompt("Please choose an environment")
        test_env.get_collaborators().summary().assert_value("run_env", RunEnvironment.Local)

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._run_local_utilities_installation")
    def test_run_installation_on_local_env(self, run_call: mock.MagicMock) -> None:
        utilities = [TestSupportedToolings["test_util_github"], TestSupportedToolings["test_util_script"]]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._run_installation(
            fake_installer_env, RunEnv_Utilities_Tuple(RunEnvironment.Local, utilities)
        )
        Assertion.expect_call_argument(self, run_call, "env", fake_installer_env)
        Assertion.expect_call_argument(self, run_call, "utilities", utilities)

    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._run_remote_installation")
    def test_run_installation_on_remote_env(self, run_call: mock.MagicMock) -> None:
        utilities = [TestSupportedToolings["test_util_github"], TestSupportedToolings["test_util_script"]]
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
        utility = TestSupportedToolings["test_util_github"]
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._print_pre_install_summary(fake_installer_env, maybe_utility=utility)
        test_env.get_collaborators().summary().assert_show_summay_title(f"Installing Utility: {utility.display_name}")

    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._print_pre_install_summary",
        side_effect=[
            PyFn.of(TestSupportedToolings["test_util_github"]),
            PyFn.of(TestSupportedToolings["test_util_script"]),
        ],
    )
    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._notify_if_utility_already_installed",
        side_effect=[
            PyFn.of(TestSupportedToolings["test_util_github"]),
            PyFn.of(TestSupportedToolings["test_util_script"]),
        ],
    )
    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._check_if_utility_already_installed",
        side_effect=[
            PyFn.of(Utility_InstallStatus_Tuple(TestSupportedToolings["test_util_github"], True)),
            PyFn.of(Utility_InstallStatus_Tuple(TestSupportedToolings["test_util_script"], False)),
        ],
    )
    def test_run_local_utilities_installation_chain_success(
        self, check_call: mock.MagicMock, notify_call: mock.MagicMock, install_call: mock.MagicMock
    ) -> None:
        utility_github = TestSupportedToolings["test_util_github"]
        utility_script = TestSupportedToolings["test_util_script"]
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
        self.assertEqual(2, install_call.call_count)
        install_call.assert_has_calls(
            any_order=False,
            calls=[
                mock.call(fake_installer_env, utility_github),
                mock.call(fake_installer_env, utility_script),
            ],
        )

    def test_check_if_utility_already_installed(self) -> None:
        utility = TestSupportedToolings["test_util_github"]
        test_env = TestEnv.create()
        test_env.get_collaborators().checks().mock_utility(utility.binary_name, exist=True)
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._check_if_utility_already_installed(fake_installer_env, utility)
        Assertion.expect_equal_objects(self, result, Utility_InstallStatus_Tuple(utility=utility, installed=True))
        test_env.get_collaborators().checks().assert_is_tool_exist(name=utility.binary_name, exist=True)

    def test_notify_if_utility_already_installed(self) -> None:
        utility = TestSupportedToolings["test_util_github"]
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._notify_if_utility_already_installed(
            fake_installer_env, utility, exists=True
        )
        self.assertIsNone(result)
        test_env.get_collaborators().printer().assert_output(
            message=f"Utility already installed locally. name: {utility.binary_name}"
        )

    def test_do_not_notify_if_utility_not_installed(self) -> None:
        utility = TestSupportedToolings["test_util_github"]
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
        utility = TestSupportedToolings["test_util_script"]
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
        utility = TestSupportedToolings["test_util_github"]
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
        utility = TestSupportedToolings["test_util_script"]
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._install_from_script(fake_installer_env, utility)
        test_env.get_collaborators().process().assert_run_command(args=[utility.sources.script.install_cmd])
        Assertion.expect_equal_objects(self, result, utility)

    def test_resolve_utility_version_when_version_is_defined(self) -> None:
        utility = TestSupportedToolings["test_util_script"]
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
        utility = TestSupportedToolings["test_util_github"]
        test_env = TestEnv.create()
        test_env.get_collaborators().github().mock_get_latest_version(
            owner=utility.sources.github.owner, repo=utility.sources.github.repo, version=utility.version
        )
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._try_resolve_version_from_github(fake_installer_env, utility)
        test_env.get_collaborators().github().assert_get_latest_version(
            owner=utility.sources.github.owner, repo=utility.sources.github.repo, version=utility.version
        )
        Assertion.expect_equal_objects(self, result, Utility_Version_Tuple(utility, utility.version))

    def test_try_resolve_version_from_github_fail(self) -> None:
        utility = TestSupportedToolings["test_util_github"]
        test_env = TestEnv.create()
        test_env.get_collaborators().github().mock_get_latest_version(
            owner=utility.sources.github.owner, repo=utility.sources.github.repo, version=None
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
        release_filename = utility.sources.github.release_name_resolver(
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
        utility = TestSupportedToolings["test_util_github"]
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
            TestSupportedToolings["test_util_github"],
            TestSupportedToolings["test_util_github"].version,
            "http://download-url.com",
        ),
    )
    def test_print_before_downloading(self, run_call: mock.MagicMock) -> None:
        utility = TestSupportedToolings["test_util_github"]
        fake_installer_env = self.create_fake_installer_env(self.env)
        eval = self.create_evaluator(fake_installer_env)
        expected_tuple = Utility_Version_ReleaseFileName_Tuple(utility, utility.version, "http://download-url.com")
        result = eval << self.get_runner(eval)._print_before_downloading(fake_installer_env, expected_tuple)
        Assertion.expect_call_argument(self, run_call, "util_ver_name_tuple", expected_tuple)
        Assertion.expect_equal_objects(self, result, expected_tuple)

    def test_print_github_binary_info(self) -> None:
        test_env = TestEnv.create()
        utility = TestSupportedToolings["test_util_github"]
        fake_installer_env = self.create_fake_installer_env(test_env)
        expected_tuple = Utility_Version_ReleaseFileName_Tuple(utility, utility.version, "http://download-url.com")
        UtilityInstallerCmdRunner(test_env.get_context())._print_github_binary_info(fake_installer_env, expected_tuple)
        test_env.get_collaborators().printer().assert_outputs(
            messages=[
                utility.sources.github.owner,
                utility.sources.github.repo,
                utility.version,
                "http://download-url.com",
            ]
        )

    def test_download_binary_by_version(self) -> None:
        test_env = TestEnv.create()
        utility = TestSupportedToolings["test_util_github"]
        release_filename = utility.sources.github.release_name_resolver(utility.version, "test-os", "test-arch")
        dl_folderpath = f"{ProvisionerInstallableBinariesPath}/{utility.binary_name}/{utility.version}"
        dl_filepath = f"{dl_folderpath}/{release_filename}"
        expected_input = Utility_Version_ReleaseFileName_Tuple(utility, utility.version, release_filename)
        expected_output = ReleaseFilename_ReleaseDownloadFilePath_Utility_Tuple(release_filename, dl_filepath, utility)
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._download_binary_by_version(fake_installer_env, expected_input)
        Assertion.expect_equal_objects(self, result, expected_output)
        test_env.get_collaborators().github().assert_download_binary(
            utility.sources.github.owner, utility.sources.github.repo, utility.version, release_filename, dl_folderpath
        )

    def test_maybe_extract_downloaded_binary_success_with_archive(self) -> None:
        utility = TestSupportedToolings["test_util_github"]
        test_env = TestEnv.create()
        release_filename = utility.sources.github.release_name_resolver(
            utility.version, test_env.get_context().os_arch.os, test_env.get_context().os_arch.arch
        )
        unpacked_release_folderpath = f"/home/user/provisioner/binaries/{utility.binary_name}/{utility.version}"
        release_download_filepath = f"{unpacked_release_folderpath}/{release_filename}"
        expected_input = ReleaseFilename_ReleaseDownloadFilePath_Utility_Tuple(
            release_filename, release_download_filepath, utility
        )
        test_env.get_collaborators().io_utils().mock_is_archive(release_download_filepath, is_archive=True)
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._maybe_extract_downloaded_binary(fake_installer_env, expected_input)
        Assertion.expect_equal_objects(
            self, result, UnpackedReleaseFolderPath_Utility_Tuple(unpacked_release_folderpath, utility)
        )
        test_env.get_collaborators().io_utils().assert_is_archive(release_download_filepath, is_archive=True)
        test_env.get_collaborators().io_utils().assert_unpack_archive(release_download_filepath)

    def test_maybe_extract_downloaded_binary_success_with_regular_file(self) -> None:
        utility = TestSupportedToolings["test_util_github"]
        test_env = TestEnv.create()
        release_filename = utility.sources.github.release_name_resolver(
            utility.version, test_env.get_context().os_arch.os, test_env.get_context().os_arch.arch
        )
        unpacked_release_folderpath = f"/home/user/provisioner/binaries/{utility.binary_name}/{utility.version}"
        release_download_filepath = f"{unpacked_release_folderpath}/{release_filename}"
        expected_input = ReleaseFilename_ReleaseDownloadFilePath_Utility_Tuple(
            release_filename, release_download_filepath, utility
        )
        test_env.get_collaborators().io_utils().mock_is_archive(release_download_filepath, is_archive=False)
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._maybe_extract_downloaded_binary(fake_installer_env, expected_input)
        Assertion.expect_equal_objects(
            self, result, UnpackedReleaseFolderPath_Utility_Tuple(unpacked_release_folderpath, utility)
        )
        test_env.get_collaborators().io_utils().assert_is_archive(release_download_filepath, is_archive=False)

    def test_elevate_permission_and_symlink(self) -> None:
        utility = TestSupportedToolings["test_util_github"]
        test_env = TestEnv.create()
        unpacked_release_folderpath = f"/home/user/provisioner/binaries/{utility.binary_name}/{utility.version}"
        unpacked_release_binary_filepath = f"{unpacked_release_folderpath}/{utility.binary_name}"
        symlink_path = f"{ProvisionerInstallableSymlinksPath}/{utility.binary_name}"
        expected_input = UnpackedReleaseFolderPath_Utility_Tuple(unpacked_release_folderpath, utility)
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        result = eval << self.get_runner(eval)._elevate_permission_and_symlink(fake_installer_env, expected_input)
        Assertion.expect_equal_objects(self, result, symlink_path)
        test_env.get_collaborators().io_utils().assert_set_file_permissions(
            unpacked_release_binary_filepath, permissions_octal=0o111
        )
        test_env.get_collaborators().io_utils().assert_write_symlink(unpacked_release_binary_filepath, symlink_path)

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
        utility = TestSupportedToolings["test_util_github"]
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
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._map_to_utilities_list", return_value=PyFn.empty())
    @mock.patch(f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._verify_selected_utilities", return_value=PyFn.empty())
    def test_run_success(
        self,
        verify_call: mock.MagicMock,
        map_call: mock.MagicMock,
        print_call: mock.MagicMock,
        resolve_call: mock.MagicMock,
        run_call: mock.MagicMock,
    ) -> None:

        fake_installer_env = self.create_fake_installer_env(self.env)
        UtilityInstallerCmdRunner.run(fake_installer_env)
        verify_call.assert_called_once()
        map_call.assert_called_once()
        print_call.assert_called_once()
        resolve_call.assert_called_once()
        run_call.assert_called_once()

    @mock.patch(
        f"{REMOTE_MACHINE_CONNECTOR_PATH}.collect_ssh_connection_info",
        return_value=TestDataRemoteConnector.create_fake_ssh_conn_info_fn()(),
    )
    def test_collect_ssh_connection_info(self, run_call: mock.MagicMock) -> None:
        test_env = TestEnv.create()
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
        # test_env.get_collaborators().summary().assert_value(
        #     attribute_name="ssh_conn_info",
        #     value=TestDataRemoteConnector.create_fake_ssh_conn_info_fn()(),
        # )

    def test_install_on_remote_machine_with_verbose_flag_enabled(self) -> None:
        utility = TestSupportedToolings["test_util_github"]
        test_env = TestEnv.create()
        ssh_conn_info = TestDataRemoteConnector.create_fake_ssh_conn_info_fn()()
        fake_installer_env = self.create_fake_installer_env(test_env, remote_context=RemoteContext.create(verbose=True))
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._install_on_remote_machine(
            fake_installer_env, SSHConnInfo_Utility_Tuple(ssh_conn_info, utility)
        )
        test_env.get_collaborators().ansible_runner().assert_command(
            selected_hosts=TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS,
            playbook=AnsiblePlaybook(name="provisioner_wrapper", content=ANSIBLE_PLAYBOOK_REMOTE_PROVISIONER_WRAPPER),
            ansible_vars=[
                f"provisioner_command='provisioner -y -v install cli --environment=Local {utility.binary_name}'",
                "required_plugins=['provisioner_installers_plugin:0.1.0']",
                "git_access_token=top-secret",
            ],
            ansible_tags=["provisioner_wrapper"],
        )

    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._install_on_remote_machine",
        side_effect=[
            PyFn.of(f"Installed {TestSupportedToolings['test_util_github'].binary_name}"),
            PyFn.of(f"Installed {TestSupportedToolings['test_util_script'].binary_name}"),
        ],
    )
    @mock.patch(
        f"{UTILITY_INSTALLER_CMD_RUNNER_PATH}._collect_ssh_connection_info",
        return_value=PyFn.of(TestDataRemoteConnector.create_fake_ssh_conn_info_fn()()),
    )
    def test_run_remote_installation_success(self, collect_call: mock.MagicMock, install_call: mock.MagicMock) -> None:
        utility_github = TestSupportedToolings["test_util_github"]
        utility_script = TestSupportedToolings["test_util_script"]
        test_env = TestEnv.create()
        fake_installer_env = self.create_fake_installer_env(test_env)
        eval = self.create_evaluator(fake_installer_env)
        eval << self.get_runner(eval)._run_remote_installation(fake_installer_env, [utility_github, utility_script])
        self.assertEqual(1, collect_call.call_count)
        self.assertEqual(2, install_call.call_count)
        test_env.get_collaborators().printer().assert_outputs(
            [
                f"Installed {TestSupportedToolings['test_util_github'].binary_name}",
                f"Installed {TestSupportedToolings['test_util_script'].binary_name}",
            ]
        )

    def test_generate_installer_welcome_with_environment(self) -> None:
        utilities = [TestSupportedToolings["test_util_github"], TestSupportedToolings["test_util_script"]]
        output = generate_installer_welcome(utilities_to_install=utilities, environment=None)
        self.assertIn("Environment was not set, you will be prompted to select a local/remote environment.", output)

    def test_generate_installer_welcome_without_environment(self) -> None:
        utilities = [TestSupportedToolings["test_util_github"], TestSupportedToolings["test_util_script"]]
        env_in_test = RunEnvironment.Local
        output = generate_installer_welcome(utilities_to_install=utilities, environment=env_in_test)
        self.assertIn(f"Running on [yellow]{env_in_test}[/yellow] environment.", output)
