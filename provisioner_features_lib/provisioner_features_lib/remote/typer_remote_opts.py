#!/usr/bin/env python3

from typing import List, Optional

import typer
from loguru import logger
from python_core_lib.cli.typer_callbacks import exclusivity_callback
from python_core_lib.runner.ansible.ansible import HostIpPair

from provisioner_features_lib.remote.domain.config import RemoteConfig, RunEnvironment

REMOTE_ONLY_HELP_TITLE = "Remote Only"


class TyperRemoteOpts:
    """
    Load method MUST be called to populate the config object after values were
    read from local configuration file
    """

    # Static variable
    remote_config: RemoteConfig

    def __init__(self, remote_config: RemoteConfig = None) -> None:
        self.remote_config = remote_config

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
            None,
            show_default=False,
            help="Remote node username",
            envvar="NODE_USERNAME",
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )

    @staticmethod
    def node_password():
        return typer.Option(
            None,
            show_default=False,
            help="Remote node password",
            envvar="NODE_PASSWORD",
            callback=exclusivity_callback,
            rich_help_panel=REMOTE_ONLY_HELP_TITLE,
        )

    @staticmethod
    def ssh_private_key_file_path():
        return typer.Option(
            None,
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

    _environment: Optional[RunEnvironment] = None
    _node_username: Optional[str] = None
    _node_password: Optional[str] = None
    _ssh_private_key_file_path: Optional[str] = None
    _ip_discovery_range: Optional[str] = None
    _remote_hosts: Optional[dict[str, RemoteConfig.Host]] = None

    def __init__(
        self,
        environment: RunEnvironment,
        node_username: Optional[str],
        node_password: Optional[str],
        ssh_private_key_file_path: Optional[str],
        ip_discovery_range: Optional[str],
        remote_hosts: dict[str, RemoteConfig.Host] = None,
    ) -> None:

        self._environment = environment
        self._node_username = node_username
        self._node_password = node_password
        self._ssh_private_key_file_path = ssh_private_key_file_path
        self._ip_discovery_range = ip_discovery_range
        self._remote_hosts = remote_hosts

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
            global _typer_cli_remote_opts
            _typer_cli_remote_opts = TyperResolvedRemoteOpts(
                environment, node_username, node_password, ssh_private_key_file_path, ip_discovery_range, remote_hosts
            )

        except Exception as e:
            e_name = e.__class__.__name__
            logger.critical("Failed to create CLI remote args object. ex: {}, message: {}", e_name, str(e))

    @staticmethod
    def environment() -> Optional[RunEnvironment]:
        return TyperResolvedRemoteOpts._environment

    @staticmethod
    def node_username() -> Optional[str]:
        return TyperResolvedRemoteOpts._node_username

    @staticmethod
    def node_password() -> Optional[str]:
        return TyperResolvedRemoteOpts._node_password

    @staticmethod
    def ssh_private_key_file_path() -> Optional[str]:
        return TyperResolvedRemoteOpts._ssh_private_key_file_path

    @staticmethod
    def ip_discovery_range() -> Optional[str]:
        return TyperResolvedRemoteOpts._ip_discovery_range

    @staticmethod
    def remote_hosts() -> Optional[str]:
        return TyperResolvedRemoteOpts._remote_hosts


_typer_cli_remote_opts: TyperResolvedRemoteOpts = None


class CliRemoteOpts:

    environment: Optional[RunEnvironment]
    node_username: Optional[str]
    node_password: Optional[str]
    ssh_private_key_file_path: Optional[str]
    ip_discovery_range: Optional[str]

    # Calculated
    host_ip_pairs: List[HostIpPair]

    def __init__(self, 
        environment: Optional[RunEnvironment] = TyperResolvedRemoteOpts.environment(),
        node_username: Optional[str] = TyperResolvedRemoteOpts.node_username(),
        node_password: Optional[str] = TyperResolvedRemoteOpts.node_password(),
        ssh_private_key_file_path: Optional[str] = TyperResolvedRemoteOpts.ssh_private_key_file_path(),
        ip_discovery_range: Optional[str] = TyperResolvedRemoteOpts.ip_discovery_range(),
        remote_hosts: Optional[dict[str, RemoteConfig.Host]] = TyperResolvedRemoteOpts.remote_hosts()) -> None:

        self.environment = environment
        self.node_username = node_username 
        self.node_password = node_password
        self.ssh_private_key_file_path = ssh_private_key_file_path
        self.ip_discovery_range = ip_discovery_range
        self.host_ip_pairs = self._to_host_ip_pairs(remote_hosts)

    @staticmethod
    def maybe_get() -> "CliRemoteOpts":
        if _typer_cli_remote_opts:
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
