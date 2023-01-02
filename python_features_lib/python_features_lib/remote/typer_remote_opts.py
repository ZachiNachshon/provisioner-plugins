#!/usr/bin/env python3

from typing import List, Optional

import typer
from loguru import logger
from python_core_lib.cli.typer_callbacks import exclusivity_callback
from python_core_lib.runner.ansible.ansible import HostIpPair

from python_features_lib.remote.domain.config import RemoteConfig, RunEnvironment

REMOTE_ONLY_HELP_TITLE = "Remote Only"


class TyperRemoteOpts:
    """
    Load method MUST be called to populate the config object after values were
    read from local configuration file
    """

    # Static variable
    remote_config: RemoteConfig

    @staticmethod
    def load(remote_config: RemoteConfig) -> None:
        TyperRemoteOpts.remote_config = remote_config

    @staticmethod
    def environment():
        return typer.Option(
            None,
            show_default=False,
            help="Specify an environment or select from a list if none supplied",
            envvar="RUN_ENVIRONMENT",
        )

    @staticmethod
    def node_username():
        return typer.Option(
            TyperRemoteOpts.remote_config.auth.node_username,
            help="Remote node username",
            envvar="NODE_USERNAME",
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )

    @staticmethod
    def node_password():
        return typer.Option(
            TyperRemoteOpts.remote_config.auth.node_password,
            help="Remote node password",
            envvar="NODE_PASSWORD",
            callback=exclusivity_callback,
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )

    @staticmethod
    def ssh_private_key_file_path():
        return typer.Option(
            TyperRemoteOpts.remote_config.auth.ssh_private_key_file_path,
            show_default=False,
            help="Private SSH key local file path",
            envvar="SSH_PRIVATE_KEY_FILE_PATH",
            callback=exclusivity_callback,
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )

    @staticmethod
    def ip_discovery_range():
        return typer.Option(
            TyperRemoteOpts.remote_config.lan_scan.ip_discovery_range,
            help="LAN network IP discovery range",
            envvar="IP_DISCOVERY_RANGE",
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )


class TyperResolvedRemoteOpts:

    environment: Optional[RunEnvironment]
    node_username: Optional[str]
    node_password: Optional[str]
    ssh_private_key_file_path: Optional[str]
    ip_discovery_range: Optional[str]
    remote_hosts: Optional[dict[str, RemoteConfig.Host]]

    def __init__(
        self,
        environment: RunEnvironment,
        node_username: Optional[str],
        node_password: Optional[str],
        ssh_private_key_file_path: Optional[str],
        ip_discovery_range: Optional[str],
        remote_hosts: dict[str, RemoteConfig.Host] = None,
    ) -> None:

        self.environment = environment
        self.node_username = node_username
        self.node_password = node_password
        self.ssh_private_key_file_path = ssh_private_key_file_path
        self.ip_discovery_range = ip_discovery_range
        self.remote_hosts = remote_hosts

    @staticmethod
    def create(
        environment: Optional[RunEnvironment] = None,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ssh_private_key_file_path: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
        remote_hosts: dict[str, RemoteConfig.Host] = None,
    ) -> None:

        try:
            global typer_cli_remote_opts
            typer_cli_remote_opts = TyperResolvedRemoteOpts(
                environment, node_username, node_password, ssh_private_key_file_path, ip_discovery_range, remote_hosts
            )

        except Exception as e:
            e_name = e.__class__.__name__
            logger.critical("Failed to create CLI remote args object. ex: {}, message: {}", e_name, str(e))

    @staticmethod
    def environment() -> Optional[RunEnvironment]:
        return typer_cli_remote_opts.environment

    @staticmethod
    def node_username() -> Optional[str]:
        return typer_cli_remote_opts.node_username

    @staticmethod
    def node_password() -> Optional[str]:
        return typer_cli_remote_opts.node_password

    @staticmethod
    def ssh_private_key_file_path() -> Optional[str]:
        return typer_cli_remote_opts.ssh_private_key_file_path

    @staticmethod
    def ip_discovery_range() -> Optional[str]:
        return typer_cli_remote_opts.ip_discovery_range

    @staticmethod
    def remote_hosts() -> Optional[str]:
        return typer_cli_remote_opts.remote_hosts


typer_cli_remote_opts: TyperResolvedRemoteOpts = None


class CliRemoteOpts:
    environment: Optional[RunEnvironment]
    node_username: Optional[str]
    node_password: Optional[str]
    ssh_private_key_file_path: Optional[str]
    ip_discovery_range: Optional[str]

    # Calculated
    host_ip_pairs: List[HostIpPair]

    def __init__(self) -> None:
        self.environment = TyperResolvedRemoteOpts.environment()
        self.node_username = TyperResolvedRemoteOpts.node_username()
        self.node_password = TyperResolvedRemoteOpts.node_password()
        self.ssh_private_key_file_path = TyperResolvedRemoteOpts.ssh_private_key_file_path()
        self.ip_discovery_range = TyperResolvedRemoteOpts.ip_discovery_range()
        self.host_ip_pairs = self._to_host_ip_pairs(TyperResolvedRemoteOpts.remote_hosts())

    @staticmethod
    def maybe_get() -> "CliRemoteOpts":
        if typer_cli_remote_opts:
            return CliRemoteOpts()
        return None

    def _to_host_ip_pairs(self, hosts: dict[str, RemoteConfig.Host]) -> List[HostIpPair]:
        if not hosts:
            return None
        result: List[HostIpPair] = []
        for key, value in hosts.items():
            result.append(HostIpPair(value.name, value.address))
        return result

    def print(self) -> None:
        logger.debug(
            f"CliRemoteOpts: \n"
            + f"  environment: {self.environment}\n"
            + f"  node_username: {self.node_username}\n"
            + f"  node_password: {self.node_password}\n"
            + f"  ip_discovery_range: {self.ip_discovery_range}\n"
            + f"  ssh_private_key_file_path: {self.ssh_private_key_file_path}\n"
            + f"  host_ip_pairs: {'supplied via CLI arguments or user config' if self.host_ip_pairs is not None else None}\n"
        )
