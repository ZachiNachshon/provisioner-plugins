#!/usr/bin/env python3

import unittest
from typing import Callable, List
from unittest import mock

from provisioner_single_board_plugin.src.common.remote.remote_os_configure import (
    ANSIBLE_PLAYBOOK_RPI_CONFIGURE_NODE,
    RemoteMachineOsConfigureArgs,
    RemoteMachineOsConfigureRunner,
    generate_instructions_post_configure,
    generate_instructions_pre_configure,
)

from provisioner_shared.components.remote.remote_connector import SSHConnectionInfo
from provisioner_shared.components.remote.remote_connector_fakes import (
    TestDataRemoteConnector,
)
from provisioner_shared.components.remote.remote_opts_fakes import TestDataRemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.infra.remote_context import RemoteContext
from provisioner_shared.components.runtime.runner.ansible.ansible_fakes import FakeAnsibleRunnerLocal
from provisioner_shared.components.runtime.runner.ansible.ansible_runner import (
    AnsiblePlaybook,
)
from provisioner_shared.components.runtime.utils.os import LINUX, MAC_OS, WINDOWS, OsArch
from provisioner_shared.components.runtime.utils.prompter import PromptLevel
from provisioner_shared.test_lib.assertions import Assertion
from provisioner_shared.test_lib.test_env import TestEnv

# To run as a single test target:
#  ./run_tests.py plugins/provisioner_single_board_plugin/provisioner_single_board_plugin/src/common/remote/remote_os_configure_test.py
#
ARG_NODE_USERNAME = "test-username"
ARG_NODE_PASSWORD = "test-password"
ARG_IP_DISCOVERY_RANGE = "1.1.1.1/24"
ARG_IP_DISCOVERY_DNS_SERVER = "1.1.1.1"

REMOTE_NETWORK_CONFIGURE_RUNNER_PATH = (
    "provisioner_single_board_plugin.src.common.remote.remote_os_configure.RemoteMachineOsConfigureRunner"
)

REMOTE_CONTEXT = RemoteContext.create(verbose=True, dry_run=False, silent=False)


class RemoteMachineConfigureTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_configure_args(self) -> RemoteMachineOsConfigureArgs:
        return RemoteMachineOsConfigureArgs(
            remote_opts=TestDataRemoteOpts.create_fake_cli_remote_opts(remote_context=REMOTE_CONTEXT),
        )

    # def test_prerequisites_fail_missing_utility(self) -> None:
    #     fake_checks = FakeChecks.create(self.env.get_context())
    #     fake_checks.on("check_tool_fn", str).side_effect = MissingUtilityException()
    #     Assertion.expect_raised_failure(
    #         self,
    #         ex_type=MissingUtilityException,
    #         method_to_run=lambda: RemoteMachineOsConfigureRunner()._prerequisites(
    #             self.env.get_context(),
    #             fake_checks,
    #         ),
    #     )

    def test_prerequisites_darwin_success(self) -> None:
        Assertion.expect_success(
            self,
            method_to_run=lambda: RemoteMachineOsConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release")),
                None,
            ),
        )

    def test_prerequisites_linux_success(self) -> None:
        Assertion.expect_success(
            self,
            method_to_run=lambda: RemoteMachineOsConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release")),
                None,
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
    @mock.patch(f"{REMOTE_NETWORK_CONFIGURE_RUNNER_PATH}._get_ssh_conn_info")
    @mock.patch(f"{REMOTE_NETWORK_CONFIGURE_RUNNER_PATH}._run_ansible_configure_os_playbook_with_progress_bar")
    @mock.patch(f"{REMOTE_NETWORK_CONFIGURE_RUNNER_PATH}._print_post_run_instructions")
    def test_main_flow_run_actions_have_expected_order(
        self,
        post_run_call: mock.MagicMock,
        run_ansible_call: mock.MagicMock,
        get_ssh_conn_info_call: mock.MagicMock,
        pre_run_call: mock.MagicMock,
        prerequisites_call: mock.MagicMock,
    ) -> None:
        env = TestEnv.create()
        RemoteMachineOsConfigureRunner().run(
            env.get_context(), self.create_fake_configure_args(), env.get_collaborators()
        )
        prerequisites_call.assert_called_once()
        pre_run_call.assert_called_once()
        get_ssh_conn_info_call.assert_called_once()
        run_ansible_call.assert_called_once()
        post_run_call.assert_called_once()

    @mock.patch(
        target="provisioner_shared.components.remote.remote_connector.RemoteMachineConnector.collect_ssh_connection_info",
        return_value=TestDataRemoteConnector.create_fake_ssh_conn_info(),
    )
    def test_get_ssh_conn_info_with_summary(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        env.get_collaborators().summary().on("append", str, SSHConnectionInfo).side_effect = (
            lambda attribute_name, value: self.assertEqual(attribute_name, "ssh_conn_info")
        )

        RemoteMachineOsConfigureRunner()._get_ssh_conn_info(env.get_context(), env.get_collaborators())
        Assertion.expect_call_argument(self, run_call, arg_name="force_single_conn_info", expected_value=True)

    def test_ansible_os_configure_playbook_run_success(self) -> None:
        env = TestEnv.create()

        env.get_collaborators().summary().on("show_summary_and_prompt_for_enter", str).side_effect = (
            lambda title: self.assertEqual(title, "Configure OS")
        )
        env.get_collaborators().progress_indicator().get_status().on(
            "long_running_process_fn", Callable, str, str
        ).return_value = "Test Output"
        env.get_collaborators().printer().on("new_line_fn", int).side_effect = None
        env.get_collaborators().printer().on("print_fn", str).side_effect = lambda message: self.assertEqual(
            message, "Test Output"
        )

        RemoteMachineOsConfigureRunner()._run_ansible_configure_os_playbook_with_progress_bar(
            ctx=env.get_context(),
            collaborators=env.get_collaborators(),
            args=self.create_fake_configure_args(),
            ssh_conn_info=TestDataRemoteConnector.create_fake_ssh_conn_info(),
        )

    def test_run_ansible(self) -> None:
        env = TestEnv.create()
        fake_runner = FakeAnsibleRunnerLocal(env.get_context())
        fake_runner.on("run_fn", List, AnsiblePlaybook, List, List, str).side_effect = (
            lambda selected_hosts, playbook, ansible_vars, ansible_tags, ansible_playbook_package: (
                self.assertEqual(selected_hosts, TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS),
                Assertion.expect_equal_objects(
                    self,
                    playbook,
                    AnsiblePlaybook(
                        name="rpi_configure_node",
                        content=ANSIBLE_PLAYBOOK_RPI_CONFIGURE_NODE,
                        remote_context=REMOTE_CONTEXT,
                    ),
                ),
                Assertion.expect_equal_objects(
                    self, ansible_vars, [f"host_name={TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1}"]
                ),
                self.assertEqual(ansible_tags, ["configure_remote_node", "reboot"]),
            )
        )

    def test_pre_run_instructions_printed_successfully(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().printer().on("print_fn", str).return_value = None
        env.get_collaborators().printer().on("print_with_rich_table_fn", str, str).side_effect = (
            lambda message, line_color: self.assertEqual(message, generate_instructions_pre_configure())
        )
        env.get_collaborators().prompter().on("prompt_for_enter_fn", PromptLevel).return_value = None
        RemoteMachineOsConfigureRunner()._print_pre_run_instructions(env.get_collaborators())

    def test_post_run_instructions_printed_successfully(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().printer().on("print_with_rich_table_fn", str, str).side_effect = (
            lambda message, line_color: (
                self.assertEqual(
                    message,
                    generate_instructions_post_configure(
                        ansible_host=TestDataRemoteConnector.TEST_DATA_ANSIBLE_HOST_1,
                    ),
                ),
            )
        )
        RemoteMachineOsConfigureRunner()._print_post_run_instructions(
            TestDataRemoteConnector.TEST_DATA_ANSIBLE_HOST_1,
            env.get_collaborators(),
        )
