#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_features_lib.remote.remote_connector import (
    DHCPCDConfigurationInfo,
    SSHConnectionInfo,
)
from provisioner_features_lib.remote.remote_connector_fakes import TestDataRemoteConnector
from python_core_lib.errors.cli_errors import MissingUtilityException
from python_core_lib.infra.context import Context
from python_core_lib.runner.ansible.ansible_fakes import FakeAnsibleRunner
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv
from python_core_lib.utils.checks_fakes import FakeChecks
from python_core_lib.utils.os import LINUX, MAC_OS, WINDOWS, OsArch

from provisioner_single_board_plugin.common.remote.remote_network_configure import (
    RemoteMachineNetworkConfigureArgs,
    RemoteMachineNetworkConfigureRunner,
)
from python_core_lib.utils.paths_fakes import FakePaths


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_single_board_plugin/common/remote/remote_network_configure_test.py
#
ARG_GW_IP_ADDRESS = "1.1.1.1"
ARG_DNS_IP_ADDRESS = "2.2.2.2"
ARG_STATIC_IP_ADDRESS = "1.1.1.200"
ARG_ANSIBLE_PLAYBOOK_RELATIVE_PATH_FROM_ROOT = "/test/path/ansible/configure_network.yaml"

class RemoteMachineNetworkConfigureTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_configure_args(self) -> RemoteMachineNetworkConfigureArgs:
        return RemoteMachineNetworkConfigureArgs(
            gw_ip_address=ARG_GW_IP_ADDRESS,
            dns_ip_address=ARG_DNS_IP_ADDRESS,
            static_ip_address=ARG_STATIC_IP_ADDRESS,
            ansible_playbook_relative_path_from_root=ARG_ANSIBLE_PLAYBOOK_RELATIVE_PATH_FROM_ROOT,
            remote_opts=None,
        )

    def test_prerequisites_fail_missing_utility(self) -> None:
        Assertion.expect_failure(
            self,
            ex_type=MissingUtilityException,
            method_to_run=lambda: RemoteMachineNetworkConfigureRunner()._prerequisites(
                self.env.get_context(),
                FakeChecks.create(self.env.get_context()).register_utility("docker", exist=False),
            ),
        )

    def test_prerequisites_darwin_success(self) -> None:
        Assertion.expect_success(
            self,
            method_to_run=lambda: RemoteMachineNetworkConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release")),
                FakeChecks.create(self.env.get_context()).register_utility("docker"),
            ),
        )

    def test_prerequisites_linux_success(self) -> None:
        Assertion.expect_success(
            self,
            method_to_run=lambda: RemoteMachineNetworkConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release")),
                FakeChecks.create(self.env.get_context()).register_utility("docker"),
            ),
        )

    def test_prerequisites_fail_on_os_not_supported(self) -> None:
        Assertion.expect_failure(
            self,
            ex_type=NotImplementedError,
            method_to_run=lambda: RemoteMachineNetworkConfigureRunner()._prerequisites(
                Context.create(os_arch=OsArch(os=WINDOWS, arch="test_arch", os_release="test_os_release")), None
            ),
        )

        Assertion.expect_failure(
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

    @mock.patch(
        "provisioner_features_lib.remote.remote_connector.RemoteMachineConnector.collect_ssh_connection_info",
        TestDataRemoteConnector.create_fake_ssh_comm_info_fn()())
    def test_get_ssh_conn_info_with_summary(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()

        env
        RemoteMachineNetworkConfigureRunner()._get_ssh_conn_info(env.get_context(), env.get_collaborators())

        run_call_kwargs = run_call.call_args.kwargs
        ctx_call_arg = run_call_kwargs["ctx"]
        cmd_call_args = run_call_kwargs["args"]

        self.assertEqual(ctx, ctx_call_arg)


    def test_ansible_network_playbook_run_success(self) -> None:
        env = TestEnv.create()

        fake_paths = FakePaths.create(env.get_context())
        fake_paths.register_custom_paths(
            path_abs_module_root=env.get_test_env_root_path(), 
            path_exec_module_root=env.get_test_env_root_path(),
            path_relative_module_root=env.get_test_env_root_path()),        
        env.collaborators.override_paths(fake_paths)

        tuple_info = RemoteMachineNetworkConfigureRunner()._run_ansible_network_configure_playbook_with_progress_bar(
            ctx=env.get_context(),
            collaborators=env.get_collaborators(),
            args=self.create_fake_configure_args(),
            get_ssh_conn_info_fn=TestDataRemoteConnector.create_fake_ssh_comm_info_fn(),
            get_dhcpcd_configure_info_fn=TestDataRemoteConnector.create_fake_get_dhcpcd_configure_info_fn(),
        )

        self.assertEqual(len(tuple_info), 2)
        self.assertIsInstance(tuple_info[0], SSHConnectionInfo)
        self.assertIsInstance(tuple_info[1], DHCPCDConfigurationInfo)

        env.collaborators.ansible_runner().assert_command(
            working_dir=env.get_test_env_root_path(),
            username=TestDataRemoteConnector.TEST_DATA_SSH_USERNAME,
            selected_hosts=TestDataRemoteConnector.TEST_DATA_SSH_HOST_IP_PAIRS,
            playbook_path=f"{env.get_test_env_root_path()}{ARG_ANSIBLE_PLAYBOOK_RELATIVE_PATH_FROM_ROOT}",
            password=TestDataRemoteConnector.TEST_DATA_SSH_PASSWORD,
            ssh_private_key_file_path=TestDataRemoteConnector.TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH,
            ansible_vars=[
                f"host_name={TestDataRemoteConnector.TEST_DATA_SSH_HOSTNAME_1}adsf",
                f"static_ip={TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS}",
                f"gateway_address={TestDataRemoteConnector.TEST_DATA_DHCP_GW_IP_ADDRESS}",
                f"dns_address={TestDataRemoteConnector.TEST_DATA_DHCP_DNS_IP_ADDRESS}",
            ],
            ansible_tags=["configure_rpi_network", "define_static_ip", "reboot"],
            extra_modules_paths=[env.get_test_env_root_path()],
            force_dockerized=False,
        )
