#!/usr/bin/env python3

import unittest
from typing import Any, Callable
from unittest import SkipTest, mock

from provisioner.errors.cli_errors import MissingUtilityException
from provisioner.infra.context import Context
from provisioner.infra.remote_context import RemoteContext
from provisioner.runner.ansible.ansible_runner import (
    AnsiblePlaybook,
)
from provisioner.test_lib import faker
from provisioner.test_lib.assertions import Assertion
from provisioner.test_lib.test_env import TestEnv
from provisioner.utils.checks_fakes import FakeChecks
from provisioner.utils.os import LINUX, MAC_OS, WINDOWS, OsArch
from provisioner.utils.printer_fakes import FakePrinter
from provisioner.utils.summary import Summary
from provisioner_features_lib.remote.remote_connector import (
    DHCPCDConfigurationInfo,
    SSHConnectionInfo,
)
from provisioner_features_lib.remote.remote_connector_fakes import (
    TestDataRemoteConnector,
)
from provisioner_features_lib.remote.typer_remote_opts_fakes import TestDataRemoteOpts

from provisioner_single_board_plugin.common.remote.remote_network_configure import (
    ANSIBLE_PLAYBOOK_RPI_CONFIGURE_NETWORK,
    RemoteMachineNetworkConfigureArgs,
    RemoteMachineNetworkConfigureRunner,
)

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_single_board_plugin/common/remote/remote_network_configure_test.py
#
ARG_GW_IP_ADDRESS = "1.1.1.1"
ARG_DNS_IP_ADDRESS = "2.2.2.2"
ARG_STATIC_IP_ADDRESS = "1.1.1.200"

REMOTE_NETWORK_CONFIGURE_RUNNER_PATH = (
    "provisioner_single_board_plugin.common.remote.remote_network_configure.RemoteMachineNetworkConfigureRunner"
)

REMOTE_CONTEXT = RemoteContext.create(verbose=True, dry_run=False, silent=False)


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

    @mock.patch(
        target="provisioner_features_lib.remote.remote_connector.RemoteMachineConnector.collect_ssh_connection_info",
        spec=TestDataRemoteConnector.create_fake_ssh_conn_info_fn(),
    )
    def test_get_ssh_conn_info_with_summary(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()

        def ssh_conn_info_side_effect(attribute_name: str, value: Any) -> bool:
            self.assertEqual(attribute_name, "ssh_conn_info")
            return None

        env.get_collaborators().summary().on("append", str, faker.Anything).side_effect = ssh_conn_info_side_effect
        RemoteMachineNetworkConfigureRunner()._get_ssh_conn_info(env.get_context(), env.get_collaborators())
        Assertion.expect_call_argument(self, run_call, arg_name="force_single_conn_info", expected_value=True)


    @mock.patch(
        target="provisioner_features_lib.remote.remote_connector.RemoteMachineConnector.collect_dhcpcd_configuration_info",
        spec=TestDataRemoteConnector.create_fake_get_dhcpcd_configure_info_fn(),
    )
    def test_get_dhcpcd_config_info_with_summary(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        args = self.create_fake_configure_args()
        ssh_conn_info = TestDataRemoteConnector.create_fake_ssh_conn_info_fn()()

        def dhcp_conn_info_side_effect(attribute_name: str, value: Any) -> bool:
            self.assertEqual(attribute_name, "dhcpcd_configure_info")
            return None
        
        env.get_collaborators().summary().on("append", str, faker.Anything).side_effect = dhcp_conn_info_side_effect
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

        def show_summary_side_effect(title: str) -> bool:
            self.assertEqual(title, "Configure Network")
            return None
        env.get_collaborators().summary().on("show_summary_and_prompt_for_enter", str).side_effect = show_summary_side_effect
        
        env.get_collaborators().progress_indicator().get_status().on("long_running_process_fn", Callable, str, str).return_value = "Test Output"
        env.get_collaborators().printer().on("new_line_fn").side_effect = None

        def print_output_side_effect(message: str) -> FakePrinter:
            self.assertEqual(message, "Test Output")
            return None
        env.get_collaborators().printer().on("print_fn", str).side_effect = print_output_side_effect

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

        Assertion.expect_success(
            self,
            method_to_run=lambda: env.get_collaborators()
            .ansible_runner()
            .assert_command(
                selected_hosts=TestDataRemoteConnector.TEST_DATA_SSH_ANSIBLE_HOSTS,
                playbook=AnsiblePlaybook(
                    name="rpi_configure_network",
                    content=ANSIBLE_PLAYBOOK_RPI_CONFIGURE_NETWORK,
                    remote_context=REMOTE_CONTEXT,
                ),
                ansible_vars=[
                    f"host_name={TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1}",
                    f"static_ip={TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS}",
                    f"gateway_address={TestDataRemoteConnector.TEST_DATA_DHCP_GW_IP_ADDRESS}",
                    f"dns_address={TestDataRemoteConnector.TEST_DATA_DHCP_DNS_IP_ADDRESS}",
                ],
                ansible_tags=["configure_rpi_network", "define_static_ip", "reboot"],
            ),
        )

    def test_add_hosts_file_entry_upon_prompt(self) -> None:
        env = TestEnv.create()
        env.get_collaborators().prompter().mock_yes_no_response("Add entry", True)
        RemoteMachineNetworkConfigureRunner()._maybe_add_hosts_file_entry(
            env.get_context(),
            (
                TestDataRemoteConnector.create_fake_ssh_conn_info_fn()(),
                TestDataRemoteConnector.create_fake_get_dhcpcd_configure_info_fn()(),
            ),
            env.get_collaborators(),
        )
        Assertion.expect_success(
            self, method_to_run=lambda: env.get_collaborators().prompter().assert_yes_no_prompt("Add entry")
        )
        Assertion.expect_success(
            self,
            method_to_run=lambda: env.get_collaborators()
            .hosts_file()
            .assert_entry_added(
                ip_address=TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS,
                dns_names=[TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1],
                comment="Added by provisioner",
            ),
        )

    @SkipTest
    def test_pre_run_instructions_printed_successfully(self) -> None:
        env = TestEnv.create()
        RemoteMachineNetworkConfigureRunner()._print_pre_run_instructions(env.get_collaborators())
        Assertion.expect_success(
            self, method_to_run=lambda: env.get_collaborators().prompter().assert_enter_prompt_count(1)
        )

    @SkipTest
    def test_post_run_instructions_printed_successfully(self) -> None:
        env = TestEnv.create()

        RemoteMachineNetworkConfigureRunner()._print_post_run_instructions(
            env.get_context(),
            (
                TestDataRemoteConnector.create_fake_ssh_conn_info_fn()(),
                TestDataRemoteConnector.create_fake_get_dhcpcd_configure_info_fn()(),
            ),
            env.get_collaborators(),
        )

        printer = env.get_collaborators().printer()
        Assertion.expect_success(
            self, method_to_run=lambda: printer.assert_output(TestDataRemoteConnector.TEST_DATA_SSH_USERNAME_1)
        )
        Assertion.expect_success(
            self, method_to_run=lambda: printer.assert_output(TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1)
        )
        Assertion.expect_success(
            self, method_to_run=lambda: printer.assert_output(TestDataRemoteConnector.TEST_DATA_SSH_IP_ADDRESS_1)
        )
        Assertion.expect_success(
            self, method_to_run=lambda: printer.assert_output(TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS)
        )
