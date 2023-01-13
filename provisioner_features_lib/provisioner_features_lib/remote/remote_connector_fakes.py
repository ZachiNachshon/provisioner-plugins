#!/usr/bin/env python3

from typing import Callable
from provisioner_features_lib.remote.remote_connector import DHCPCDConfigurationInfo, SSHConnectionInfo
from python_core_lib.runner.ansible.ansible import HostIpPair

class TestDataRemoteConnector:

    TEST_DATA_SSH_USERNAME = "test-username"
    TEST_DATA_SSH_PASSWORD = "test-password"
    TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH = "test-ssh-private-key-file-path"
    TEST_DATA_SSH_HOSTNAME_1 = "test-hostname-1"
    TEST_DATA_SSH_ADDRESS_1 = "test-ip-address-1"
    TEST_DATA_SSH_HOSTNAME_2 = "test-hostname-2"
    TEST_DATA_SSH_ADDRESS_2 = "test-ip-address-2"
    TEST_DATA_SSH_HOST_IP_PAIRS = [
        HostIpPair(TEST_DATA_SSH_HOSTNAME_1, TEST_DATA_SSH_ADDRESS_1), 
        HostIpPair(TEST_DATA_SSH_HOSTNAME_2, TEST_DATA_SSH_ADDRESS_2)
    ]
    TEST_DATA_DHCP_GW_IP_ADDRESS = "test-gw-ip-address"
    TEST_DATA_DHCP_DNS_IP_ADDRESS = "test-dns-ip-address"
    TEST_DATA_DHCP_STATIC_IP_ADDRESS = "test-static-ip-address"

    @staticmethod
    def create_fake_ssh_comm_info_fn() -> Callable[..., SSHConnectionInfo]:
        def create_fn(*any) -> SSHConnectionInfo:
            return SSHConnectionInfo(
                username=TestDataRemoteConnector.TEST_DATA_SSH_USERNAME,
                password=TestDataRemoteConnector.TEST_DATA_SSH_PASSWORD,
                ssh_private_key_file_path=TestDataRemoteConnector.TEST_DATA_SSH_PRIVATE_KEY_FILE_PATH,
                host_ip_pairs=TestDataRemoteConnector.TEST_DATA_SSH_HOST_IP_PAIRS
            )

        return create_fn

    @staticmethod
    def create_fake_get_dhcpcd_configure_info_fn() -> Callable[..., DHCPCDConfigurationInfo]:
        def create_fn(*any) -> DHCPCDConfigurationInfo:
            return DHCPCDConfigurationInfo(
                gw_ip_address=TestDataRemoteConnector.TEST_DATA_DHCP_GW_IP_ADDRESS,
                dns_ip_address=TestDataRemoteConnector.TEST_DATA_DHCP_DNS_IP_ADDRESS,
                static_ip_address=TestDataRemoteConnector.TEST_DATA_DHCP_STATIC_IP_ADDRESS,
            )

        return create_fn
