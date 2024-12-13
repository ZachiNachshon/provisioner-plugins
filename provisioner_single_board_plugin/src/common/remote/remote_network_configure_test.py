#!/usr/bin/env python3

import unittest
from typing import Callable, List
from unittest import mock

from provisioner_single_board_plugin.src.common.remote.remote_network_configure import (
    ANSIBLE_PLAYBOOK_RPI_CONFIGURE_NETWORK,
    RemoteMachineNetworkConfigureArgs,
    RemoteMachineNetworkConfigureRunner,
    generate_instructions_post_network,
    generate_instructions_pre_network,
)
from provisioner_shared.components.runtime.test_lib import faker

from provisioner_shared.components.remote.remote_connector import (
    DHCPCDConfigurationInfo,
    SSHConnectionInfo,
)
from provisioner_shared.components.remote.remote_connector_fakes import (
    TestDataRemoteConnector,
)
from provisioner_shared.components.remote.typer_remote_opts_fakes import TestDataRemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.infra.remote_context import RemoteContext
from provisioner_shared.components.runtime.runner.ansible.ansible_fakes import FakeAnsibleRunnerLocal
from provisioner_shared.components.runtime.runner.ansible.ansible_runner import (
    AnsiblePlaybook,
)
from provisioner_shared.components.runtime.test_lib.assertions import Assertion
from provisioner_shared.components.runtime.test_lib.test_env import TestEnv
from provisioner_shared.components.runtime.utils.os import LINUX, MAC_OS, WINDOWS, OsArch
from provisioner_shared.components.runtime.utils.prompter import PromptLevel

# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_single_board_plugin/src/common/remote/remote_network_configure_test.py
#
ARG_GW_IP_ADDRESS = "1.1.1.1"
ARG_DNS_IP_ADDRESS = "2.2.2.2"
ARG_STATIC_IP_ADDRESS = "1.1.1.200"

REMOTE_NETWORK_CONFIGURE_RUNNER_PATH = (
    "provisioner_single_board_plugin.src.common.remote.remote_network_configure.RemoteMachineNetworkConfigureRunner"
)

REMOTE_MACHINE_CONNECTOR_PATH = (
    "provisioner_shared.components.remote.remote_connector.RemoteMachineConnector"
)

REMOTE_CONTEXT = RemoteContext.create(verbose=True, dry_run=False, silent=False, non_interactive=False)


class RemoteMachineNetworkConfigureTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_configure_args(self) -> RemoteMachineNetworkConfigureArgs:
        return RemoteMachineNetworkConfigureArgs(
            gw_ip_address=ARG_GW_IP_ADDRESS,
            dns_ip_address=ARG_DNS_IP_ADDRESS,
            static_ip_address=ARG_STATIC_IP_ADDRESS,
            remote_opts=TestDataRemoteOpts.create_fake_cli_remote_opts(remote_context=REMOTE_CONTEXT),
        )

    def create_fake_network_info_bundle() -> RemoteMachineNetworkConfigureRunner.NetworkInfoBundle:
        return RemoteMachineNetworkConfigureRunner.NetworkInfoBundle(
            ssh_ip_address=TestDataRemoteConnector.TEST_DATA_SSH_IP_ADDRESS_1,
            ssh_username=TestDataRemoteConnector.TEST_DATA_SSH_USERNAME_1,
            ssh_hostname=TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1,
            static_ip_address=TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS,
        )

    # def test_prerequisites_fail_missing_utility(self) -> None:
    #     fake_checks = FakeChecks.create(self.env.get_context())
    #     fake_checks.on("check_tool_fn", str).side_effect = MissingUtilityException()
    #     Assertion.expect_raised_failure(
    #         self,
    #         ex_type=MissingUtilityException,
    #         method_to_run=lambda: RemoteMachineNetworkConfigureRunner()._prerequisites(
    #             self.env.get_context(),
    #             fake_checks,
    #         ),
    #     )

    def test_prerequisites_darwin_success(self) -> None:
        Assertion.expect_success(
            self,
            method_to_run=lambda: RemoteMachineNetworkConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release")),
                None,
            ),
        )

    def test_prerequisites_linux_success(self) -> None:
        Assertion.expect_success(
            self,
            method_to_run=lambda: RemoteMachineNetworkConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release")),
                None,
            ),
        )

    def test_prerequisites_fail_on_os_not_supported(self) -> None:
        Assertion.expect_raised_failure(
            self,
            ex_type=NotImplementedError,
            method_to_run=lambda: RemoteMachineNetworkConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=WINDOWS, arch="test_arch", os_release="test_os_release")),
                None,
            ),
        )

        Assertion.expect_raised_failure(
            self,
            ex_type=NotImplementedError,
            method_to_run=lambda: RemoteMachineNetworkConfigureRunner()._prerequisites(
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
    @mock.patch(f"{REMOTE_NETWORK_CONFIGURE_RUNNER_PATH}._run_ansible_network_configure_playbook_with_progress_bar")
    @mock.patch(f"{REMOTE_NETWORK_CONFIGURE_RUNNER_PATH}._print_post_run_instructions")
    @mock.patch(f"{REMOTE_NETWORK_CONFIGURE_RUNNER_PATH}._maybe_add_hosts_file_entry")
    def test_main_flow_run_actions_have_expected_order(
        self,
        maybe_add_hosts_file_call: mock.MagicMock,
        post_run_call: mock.MagicMock,
        run_ansible_call: mock.MagicMock,
        pre_run_call: mock.MagicMock,
        prerequisites_call: mock.MagicMock,
    ) -> None:
        env = TestEnv.create()
        RemoteMachineNetworkConfigureRunner().run(
            env.get_context(), self.create_fake_configure_args(), env.get_collaborators()
        )
        prerequisites_call.assert_called_once()
        pre_run_call.assert_called_once()
        run_ansible_call.assert_called_once()
        post_run_call.assert_called_once()
        maybe_add_hosts_file_call.assert_called_once()

    # TODO: Fix me
    @mock.patch(
        target=f"{REMOTE_MACHINE_CONNECTOR_PATH}.collect_ssh_connection_info",
        spec=TestDataRemoteConnector.create_fake_ssh_conn_info_fn(),
    )
    def test_get_ssh_conn_info_with_summary(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        env.get_collaborators().summary().on("append", str, faker.Anything).side_effect = (
            lambda attribute_name, value: self.assertEqual(attribute_name, "ssh_conn_info")
        )
        RemoteMachineNetworkConfigureRunner()._get_ssh_conn_info(env.get_context(), env.get_collaborators())
        Assertion.expect_call_argument(self, run_call, arg_name="force_single_conn_info", expected_value=True)

    @mock.patch(
        target=f"{REMOTE_MACHINE_CONNECTOR_PATH}.collect_dhcpcd_configuration_info",
        spec=TestDataRemoteConnector.create_fake_get_dhcpcd_configure_info_fn(),
    )
    def test_get_dhcpcd_config_info_with_summary(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        args = self.create_fake_configure_args()
        ssh_conn_info = TestDataRemoteConnector.create_fake_ssh_conn_info_fn()()
        env.get_collaborators().summary().on("append", str, faker.Anything).side_effect = (
            lambda attribute_name, value: self.assertEqual(attribute_name, "dhcpcd_configure_info")
        )

        RemoteMachineNetworkConfigureRunner()._get_dhcpcd_configure_info(
            env.get_context(), env.get_collaborators(), args, ssh_conn_info
        )
        Assertion.expect_call_argument(
            self, run_call, arg_name="ansible_hosts", expected_value=ssh_conn_info.ansible_hosts
        )
        Assertion.expect_call_argument(
            self, run_call, arg_name="static_ip_address", expected_value=args.static_ip_address
        )
        Assertion.expect_call_argument(self, run_call, arg_name="gw_ip_address", expected_value=args.gw_ip_address)
        Assertion.expect_call_argument(self, run_call, arg_name="dns_ip_address", expected_value=args.dns_ip_address)

    def test_ansible_network_playbook_run_success(self) -> None:
        env = TestEnv.create()

        env.get_collaborators().summary().on("show_summary_and_prompt_for_enter", str).side_effect = (
            lambda title: self.assertEqual(title, "Configure Network")
        )
        env.get_collaborators().progress_indicator().get_status().on(
            "long_running_process_fn", Callable, str, str
        ).return_value = "Test Output"
        env.get_collaborators().printer().on("new_line_fn", int).side_effect = None
        env.get_collaborators().printer().on("print_fn", str).side_effect = lambda message: self.assertEqual(
            message, "Test Output"
        )

        tuple_info = RemoteMachineNetworkConfigureRunner()._run_ansible_network_configure_playbook_with_progress_bar(
            ctx=env.get_context(),
            collaborators=env.get_collaborators(),
            args=self.create_fake_configure_args(),
            get_ssh_conn_info_fn=TestDataRemoteConnector.create_fake_ssh_conn_info_fn(),
            get_dhcpcd_configure_info_fn=TestDataRemoteConnector.create_fake_get_dhcpcd_configure_info_fn(),
        )

        self.assertEqual(len(tuple_info), 2)
        self.assertIsInstance(tuple_info[0], SSHConnectionInfo)
        self.assertIsInstance(tuple_info[1], DHCPCDConfigurationInfo)

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
                        name="rpi_configure_network",
                        content=ANSIBLE_PLAYBOOK_RPI_CONFIGURE_NETWORK,
                        remote_context=REMOTE_CONTEXT,
                    ),
                ),
                Assertion.expect_equal_objects(
                    self,
                    ansible_vars,
                    [
                        f"host_name={TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1}",
                        f"static_ip={TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS}",
                        f"gateway_address={TestDataRemoteConnector.TEST_DATA_DHCP_GW_IP_ADDRESS}",
                        f"dns_address={TestDataRemoteConnector.TEST_DATA_DHCP_DNS_IP_ADDRESS}",
                    ],
                ),
                self.assertEqual(ansible_tags, ["configure_rpi_network", "define_static_ip", "reboot"]),
            )
        )

        RemoteMachineNetworkConfigureRunner()._run_ansible(
            runner=fake_runner,
            remote_ctx=REMOTE_CONTEXT,
            ssh_hostname=TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1,
            ssh_conn_info=TestDataRemoteConnector.create_fake_ssh_conn_info_fn()(),
            dhcpcd_configure_info=TestDataRemoteConnector.create_fake_get_dhcpcd_configure_info_fn()(),
        )

    def test_add_hosts_file_entry_upon_prompt(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().prompter().on("prompt_yes_no_fn", str, PromptLevel, str, str).side_effect = (
            lambda message, level, post_yes_message, post_no_message: (
                self.assertIn("Add entry", message),
                self.assertEqual(level, PromptLevel.HIGHLIGHT),
                self.assertEqual(post_no_message, "Skipped adding new entry to /etc/hosts"),
                self.assertEqual(post_yes_message, "Selected to update /etc/hosts file"),
            )
        )
        env.get_collaborators().hosts_file().on("add_entry_fn", str, List, str, str).side_effect = (
            lambda ip_address, dns_names, comment=None, entry_type="ipv4": (
                self.assertEqual(ip_address, TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS),
                self.assertEqual(dns_names, [TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1]),
                self.assertEqual(comment, "Added by provisioner"),
                None,
            )
        )
        RemoteMachineNetworkConfigureRunner()._maybe_add_hosts_file_entry(
            env.get_context(),
            (
                TestDataRemoteConnector.create_fake_ssh_conn_info_fn()(),
                TestDataRemoteConnector.create_fake_get_dhcpcd_configure_info_fn()(),
            ),
            env.get_collaborators(),
        )

    def test_pre_run_instructions_printed_successfully(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().printer().on("print_fn", str).return_value = None
        env.get_collaborators().printer().on("print_with_rich_table_fn", str, str).side_effect = (
            lambda message, line_color: self.assertEqual(message, generate_instructions_pre_network())
        )
        env.get_collaborators().prompter().on("prompt_for_enter_fn", PromptLevel).return_value = None
        RemoteMachineNetworkConfigureRunner()._print_pre_run_instructions(env.get_collaborators())

    def test_post_run_instructions_printed_successfully(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().printer().on("print_with_rich_table_fn", str, str).side_effect = (
            lambda message, line_color: (
                self.assertEqual(
                    message,
                    generate_instructions_post_network(
                        ip_address=TestDataRemoteConnector.TEST_DATA_SSH_IP_ADDRESS_1,
                        static_ip=TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS,
                        username=TestDataRemoteConnector.TEST_DATA_SSH_USERNAME_1,
                        hostname=TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1,
                    ),
                ),
            )
        )
        RemoteMachineNetworkConfigureRunner()._print_post_run_instructions(
            env.get_context(),
            (
                TestDataRemoteConnector.create_fake_ssh_conn_info_fn()(),
                TestDataRemoteConnector.create_fake_get_dhcpcd_configure_info_fn()(),
            ),
            env.get_collaborators(),
        )
