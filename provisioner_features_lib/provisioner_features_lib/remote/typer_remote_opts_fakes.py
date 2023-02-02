#!/usr/bin/env python3

from provisioner_features_lib.remote.domain.config import RemoteConfig, RunEnvironment
from provisioner_features_lib.remote.typer_remote_opts import (
    CliRemoteOpts,
    TyperRemoteOpts,
)


class TestDataRemoteOpts:
    TEST_DATA_ENVIRONMENT: RunEnvironment = RunEnvironment.Local
    TEST_DATA_SSH_HOSTNAME_1 = "test-hostname-1"
    TEST_DATA_SSH_HOSTNAME_2 = "test-hostname-2"
    TEST_DATA_SSH_IP_ADDRESS_1 = "test-ip-address-1"
    TEST_DATA_SSH_IP_ADDRESS_2 = "test-ip-address-2"
    TEST_DATA_REMOTE_NODE_USERNAME_1 = "test-user-1"
    TEST_DATA_REMOTE_NODE_USERNAME_2 = "test-user-2"
    TEST_DATA_REMOTE_NODE_PASSWORD_1 = "test-pass-1"
    TEST_DATA_REMOTE_NODE_PASSWORD_2 = "test-pass-2"
    TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH_1 = "test-ssh-private-key-1"
    TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH_2 = "test-ssh-private-key-2"
    TEST_DATA_REMOTE_IP_DISCOVERY_RANGE = "1.1.1.1/32"

    TEST_REMOTE_HOSTS_DICT = {
        TEST_DATA_SSH_HOSTNAME_1: RemoteConfig.Host(
            host=TEST_DATA_SSH_HOSTNAME_1,
            address=TEST_DATA_SSH_IP_ADDRESS_1,
            auth=RemoteConfig.Host.Auth(
                username=TEST_DATA_REMOTE_NODE_USERNAME_1,
                password=TEST_DATA_REMOTE_NODE_PASSWORD_1,
                # Mutually exclusive with ssh_private_key_file_path
            ),
        ),
        TEST_DATA_SSH_HOSTNAME_1: RemoteConfig.Host(
            host=TEST_DATA_SSH_HOSTNAME_1,
            address=TEST_DATA_SSH_IP_ADDRESS_2,
            auth=RemoteConfig.Host.Auth(
                username=TEST_DATA_REMOTE_NODE_USERNAME_2,
                # Mutually exclusive with node_password
                ssh_private_key_file_path=TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH_2,
            ),
        ),
    }

    @staticmethod
    def create_fake_remote_opts() -> TyperRemoteOpts:
        return TyperRemoteOpts(
            remote_config=RemoteConfig(
                lan_scan=RemoteConfig.LanScan(TestDataRemoteOpts.TEST_DATA_REMOTE_IP_DISCOVERY_RANGE),
                hosts=TestDataRemoteOpts.TEST_REMOTE_HOSTS_DICT,
            )
        )

    @staticmethod
    def create_fake_cli_remote_opts() -> CliRemoteOpts:
        return CliRemoteOpts(
            environment=TestDataRemoteOpts.TEST_DATA_ENVIRONMENT,
            node_username=TestDataRemoteOpts.TEST_DATA_REMOTE_NODE_USERNAME_1,
            node_password=TestDataRemoteOpts.TEST_DATA_REMOTE_NODE_PASSWORD_1,
            ssh_private_key_file_path=TestDataRemoteOpts.TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH_1,
            ip_discovery_range=TestDataRemoteOpts.TEST_DATA_REMOTE_IP_DISCOVERY_RANGE,
            remote_hosts=TestDataRemoteOpts.TEST_REMOTE_HOSTS_DICT,
        )
