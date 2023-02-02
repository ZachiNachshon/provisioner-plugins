#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_features_lib.remote.remote_connector_fakes import (
    TestDataRemoteConnector,
)
from python_core_lib.errors.cli_errors import MissingUtilityException
from python_core_lib.infra.context import Context
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv
from python_core_lib.utils.checks_fakes import FakeChecks
from python_core_lib.utils.os import LINUX, MAC_OS, WINDOWS, OsArch

from provisioner_single_board_plugin.common.remote.remote_os_configure import (
    RemoteMachineOsConfigureArgs,
    RemoteMachineOsConfigureRunner,
)

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_single_board_plugin/common/remote/remote_os_configure_test.py
#
ARG_NODE_USERNAME = "test-username"
ARG_NODE_PASSWORD = "test-password"
ARG_IP_DISCOVERY_RANGE = "1.1.1.1/24"
ARG_ANSIBLE_PLAYBOOK_RELATIVE_PATH_FROM_ROOT = "/test/path/ansible/os_configure.yaml"

REMOTE_NETWORK_CONFIGURE_RUNNER_PATH = (
    "provisioner_single_board_plugin.common.remote.remote_os_configure.RemoteMachineOsConfigureRunner"
)


class RemoteMachineConfigureTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_configure_args(self) -> RemoteMachineOsConfigureArgs:
        return RemoteMachineOsConfigureArgs(
            ansible_playbook_relative_path_from_root=ARG_ANSIBLE_PLAYBOOK_RELATIVE_PATH_FROM_ROOT,
            remote_opts=None,
        )

    def test_prerequisites_fail_missing_utility(self) -> None:
        Assertion.expect_raised_failure(
            self,
            ex_type=MissingUtilityException,
            method_to_run=lambda: RemoteMachineOsConfigureRunner()._prerequisites(
                self.env.get_context(),
                FakeChecks.create(self.env.get_context()).mock_utility("docker", exist=False),
            ),
        )

    def test_prerequisites_darwin_success(self) -> None:
        Assertion.expect_success(
            self,
            method_to_run=lambda: RemoteMachineOsConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release")),
                FakeChecks.create(self.env.get_context()).mock_utility("docker"),
            ),
        )

    def test_prerequisites_linux_success(self) -> None:
        Assertion.expect_success(
            self,
            method_to_run=lambda: RemoteMachineOsConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release")),
                FakeChecks.create(self.env.get_context()).mock_utility("docker"),
            ),
        )

    def test_prerequisites_fail_on_os_not_supported(self) -> None:
        Assertion.expect_raised_failure(
            self,
            ex_type=NotImplementedError,
            method_to_run=lambda: RemoteMachineOsConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=WINDOWS, arch="test_arch", os_release="test_os_release")), None
            ),
        )

        Assertion.expect_raised_failure(
            self,
            ex_type=NotImplementedError,
            method_to_run=lambda: RemoteMachineOsConfigureRunner()._prerequisites(
                Context.create(
                    os_arch=OsArch(os="NOT-SUPPORTED", arch="test_arch", os_release="test_os_release"),
                    verbose=False,
                    dry_run=False,
                ),
                None,
            ),
        )

    @mock.patch(f"{REMOTE_NETWORK_CONFIGURE_RUNNER_PATH}._prerequisites")
    @mock.patch(f"{REMOTE_NETWORK_CONFIGURE_RUNNER_PATH}._print_pre_run_instructions")
    @mock.patch(f"{REMOTE_NETWORK_CONFIGURE_RUNNER_PATH}._run_ansible_configure_os_playbook_with_progress_bar")
    @mock.patch(f"{REMOTE_NETWORK_CONFIGURE_RUNNER_PATH}._print_post_run_instructions")
    def test_main_flow_run_actions_have_expected_order(
        self,
        post_run_call: mock.MagicMock,
        run_ansible_call: mock.MagicMock,
        pre_run_call: mock.MagicMock,
        prerequisites_call: mock.MagicMock,
    ) -> None:
        env = TestEnv.create()
        RemoteMachineOsConfigureRunner().run(
            env.get_context(), self.create_fake_configure_args(), env.get_collaborators()
        )
        prerequisites_call.assert_called_once()
        pre_run_call.assert_called_once()
        run_ansible_call.assert_called_once()
        post_run_call.assert_called_once()

    @mock.patch(
        target="provisioner_features_lib.remote.remote_connector.RemoteMachineConnector.collect_ssh_connection_info",
        spec=TestDataRemoteConnector.create_fake_ssh_conn_info_fn(),
    )
    def test_get_ssh_conn_info_with_summary(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        ssh_conn_info_resp = RemoteMachineOsConfigureRunner()._get_ssh_conn_info(
            env.get_context(), env.get_collaborators()
        )
        Assertion.expect_call_argument(self, run_call, arg_name="force_single_conn_info", expected_value=True)
        Assertion.expect_success(
            self,
            method_to_run=lambda: env.get_collaborators().summary().assert_value("ssh_conn_info", ssh_conn_info_resp),
        )

    def test_ansible_os_configure_playbook_run_success(self) -> None:
        env = TestEnv.create()
        RemoteMachineOsConfigureRunner()._run_ansible_configure_os_playbook_with_progress_bar(
            ctx=env.get_context(),
            collaborators=env.get_collaborators(),
            args=self.create_fake_configure_args(),
            get_ssh_conn_info_fn=TestDataRemoteConnector.create_fake_ssh_conn_info_fn(),
        )
        Assertion.expect_success(
            self,
            method_to_run=lambda: env.get_collaborators()
            .ansible_runner()
            .assert_command(
                working_dir=env.get_test_env_root_path(),
                username=TestDataRemoteConnector.TEST_DATA_SSH_USERNAME_1,
                selected_hosts=TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS,
                playbook_path=f"{env.get_test_env_root_path()}{ARG_ANSIBLE_PLAYBOOK_RELATIVE_PATH_FROM_ROOT}",
                password=TestDataRemoteConnector.TEST_DATA_SSH_PASSWORD_1,
                ssh_private_key_file_path=TestDataRemoteConnector.TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH_1,
                ansible_vars=[
                    f"host_name={TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1}",
                ],
                ansible_tags=["configure_remote_node", "reboot"],
                extra_modules_paths=[env.get_test_env_root_path()],
                force_dockerized=False,
            ),
        )

    def test_pre_run_instructions_printed_successfully(self) -> None:
        env = TestEnv.create()
        RemoteMachineOsConfigureRunner()._print_pre_run_instructions(env.get_collaborators())
        Assertion.expect_success(
            self, method_to_run=lambda: env.get_collaborators().prompter().assert_enter_prompt_count(1)
        )

    def test_post_run_instructions_printed_successfully(self) -> None:
        env = TestEnv.create()
        RemoteMachineOsConfigureRunner()._print_post_run_instructions(
            (TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1, TestDataRemoteConnector.TEST_DATA_SSH_IP_ADDRESS_1),
            env.get_collaborators(),
        )
        printer = env.get_collaborators().printer()
        Assertion.expect_success(
            self, method_to_run=lambda: printer.assert_output(TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1)
        )
        Assertion.expect_success(
            self, method_to_run=lambda: printer.assert_output(TestDataRemoteConnector.TEST_DATA_SSH_IP_ADDRESS_1)
        )
