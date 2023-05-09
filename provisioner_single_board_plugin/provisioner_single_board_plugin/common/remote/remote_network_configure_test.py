#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_features_lib.remote.remote_connector import (
    DHCPCDConfigurationInfo,
    SSHConnectionInfo,
)
from provisioner_features_lib.remote.remote_connector_fakes import (
    TestDataRemoteConnector,
)
from python_core_lib.errors.cli_errors import MissingUtilityException
from python_core_lib.infra.context import Context
from python_core_lib.runner.ansible.ansible_runner import (
    AnsiblePlaybook,
)
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv
from python_core_lib.utils.checks_fakes import FakeChecks
from python_core_lib.utils.os import LINUX, MAC_OS, WINDOWS, OsArch

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


class RemoteMachineNetworkConfigureTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_configure_args(self) -> RemoteMachineNetworkConfigureArgs:
        return RemoteMachineNetworkConfigureArgs(
            gw_ip_address=ARG_GW_IP_ADDRESS,
            dns_ip_address=ARG_DNS_IP_ADDRESS,
            static_ip_address=ARG_STATIC_IP_ADDRESS,
            remote_opts=None,
        )

    def create_fake_network_info_bundle() -> RemoteMachineNetworkConfigureRunner.NetworkInfoBundle:
        return RemoteMachineNetworkConfigureRunner.NetworkInfoBundle(
            ssh_ip_address=TestDataRemoteConnector.TEST_DATA_SSH_IP_ADDRESS_1,
            ssh_username=TestDataRemoteConnector.TEST_DATA_SSH_USERNAME_1,
            ssh_hostname=TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1,
            static_ip_address=TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS,
        )

    def test_prerequisites_fail_missing_utility(self) -> None:
        Assertion.expect_raised_failure(
            self,
            ex_type=MissingUtilityException,
            method_to_run=lambda: RemoteMachineNetworkConfigureRunner()._prerequisites(
                self.env.get_context(),
                FakeChecks.create(self.env.get_context()).mock_utility("docker", exist=False),
            ),
        )

    def test_prerequisites_darwin_success(self) -> None:
        Assertion.expect_success(
            self,
            method_to_run=lambda: RemoteMachineNetworkConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release")),
                FakeChecks.create(self.env.get_context()).mock_utility("docker"),
            ),
        )

    def test_prerequisites_linux_success(self) -> None:
        Assertion.expect_success(
            self,
            method_to_run=lambda: RemoteMachineNetworkConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release")),
                FakeChecks.create(self.env.get_context()).mock_utility("docker"),
            ),
        )

    def test_prerequisites_fail_on_os_not_supported(self) -> None:
        Assertion.expect_raised_failure(
            self,
            ex_type=NotImplementedError,
            method_to_run=lambda: RemoteMachineNetworkConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=WINDOWS, arch="test_arch", os_release="test_os_release")), None
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
        ssh_conn_info_resp = RemoteMachineNetworkConfigureRunner()._get_ssh_conn_info(
            env.get_context(), env.get_collaborators()
        )
        Assertion.expect_call_argument(self, run_call, arg_name="force_single_conn_info", expected_value=True)
        Assertion.expect_success(
            self,
            method_to_run=lambda: env.get_collaborators().summary().assert_value("ssh_conn_info", ssh_conn_info_resp),
        )

    @mock.patch(
        target="provisioner_features_lib.remote.remote_connector.RemoteMachineConnector.collect_dhcpcd_configuration_info",
        spec=TestDataRemoteConnector.create_fake_get_dhcpcd_configure_info_fn(),
    )
    def test_get_dhcpcd_config_info_with_summary(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        args = self.create_fake_configure_args()
        ssh_conn_info = TestDataRemoteConnector.create_fake_ssh_conn_info_fn()()

        dhcpcd_configure_info_resp = RemoteMachineNetworkConfigureRunner()._get_dhcpcd_configure_info(
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
        Assertion.expect_success(
            self,
            method_to_run=lambda: env.get_collaborators()
            .summary()
            .assert_value("dhcpcd_configure_info", dhcpcd_configure_info_resp),
        )

    def test_ansible_network_playbook_run_success(self) -> None:
        env = TestEnv.create()

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
                playbook=AnsiblePlaybook(name="rpi_configure_network", content=ANSIBLE_PLAYBOOK_RPI_CONFIGURE_NETWORK),
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

    def test_pre_run_instructions_printed_successfully(self) -> None:
        env = TestEnv.create()
        RemoteMachineNetworkConfigureRunner()._print_pre_run_instructions(env.get_collaborators())
        Assertion.expect_success(
            self, method_to_run=lambda: env.get_collaborators().prompter().assert_enter_prompt_count(1)
        )

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
