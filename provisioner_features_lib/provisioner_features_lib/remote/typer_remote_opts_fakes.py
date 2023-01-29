#!/usr/bin/env python3

from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts, TyperRemoteOpts

from provisioner_features_lib.remote.domain.config import RemoteConfig, RunEnvironment


class TestDataRemoteOpts:
    TEST_DATA_ENVIRONMENT: RunEnvironment = RunEnvironment.Local
    TEST_DATA_SSH_HOSTNAME = "test-hostname"
    TEST_DATA_SSH_IP_ADDRESS = "test-ip-address"
    TEST_DATA_REMOTE_NODE_USERNAME = "test-user"
    TEST_DATA_REMOTE_NODE_PASSWORD = "test-pass"
    TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH = "test-ssh-private-key"
    TEST_DATA_REMOTE_IP_DISCOVERY_RANGE = "1.1.1.1/32"

    @staticmethod
    def create_fake_remote_opts() -> TyperRemoteOpts:
        return TyperRemoteOpts(
            remote_config=RemoteConfig(
                lan_scan=RemoteConfig.LanScan(TestDataRemoteOpts.TEST_DATA_REMOTE_IP_DISCOVERY_RANGE),
                auth=RemoteConfig.Auth(
                    node_username=TestDataRemoteOpts.TEST_DATA_REMOTE_NODE_USERNAME,
                    node_password=TestDataRemoteOpts.TEST_DATA_REMOTE_NODE_PASSWORD,
                    # Mutually exclusive with node_password
                    # ssh_private_key_file_path=TestDataRemoteOpts.TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH
                ),
                hosts={
                    TestDataRemoteOpts.TEST_DATA_SSH_HOSTNAME: RemoteConfig.Host(
                        TestDataRemoteOpts.TEST_DATA_SSH_HOSTNAME, TestDataRemoteOpts.TEST_DATA_SSH_IP_ADDRESS
                    )
                }
            )
        )
    
    @staticmethod
    def create_fake_cli_remote_opts() -> CliRemoteOpts:
        return CliRemoteOpts(
            environment = TestDataRemoteOpts.TEST_DATA_ENVIRONMENT,
            node_username = TestDataRemoteOpts.TEST_DATA_REMOTE_NODE_USERNAME,
            node_password = TestDataRemoteOpts.TEST_DATA_REMOTE_NODE_PASSWORD,
            ssh_private_key_file_path = TestDataRemoteOpts.TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH,
            ip_discovery_range = TestDataRemoteOpts.TEST_DATA_REMOTE_IP_DISCOVERY_RANGE,
            remote_hosts = {
                TestDataRemoteOpts.TEST_DATA_SSH_HOSTNAME: RemoteConfig.Host(
                    TestDataRemoteOpts.TEST_DATA_SSH_HOSTNAME, TestDataRemoteOpts.TEST_DATA_SSH_IP_ADDRESS
                )
            }
        )
