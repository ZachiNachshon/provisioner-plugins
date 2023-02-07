#!/usr/bin/env python3

from typing import List, Optional

import typer
from loguru import logger
from python_core_lib.cli.typer_callbacks import exclusivity_callback
from python_core_lib.runner.ansible.ansible import AnsibleHost

from provisioner_features_lib.remote.domain.config import RemoteConfig, RunEnvironment

REMOTE_ONLY_HELP_TITLE = "Remote Only"


class TyperRemoteOpts:
    """
    Load method MUST be called to populate the config object after values were
    read from local configuration file
    """

    # Static variable
    remote_config: RemoteConfig = None

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

        global GLOBAL_TYPER_RESOLVED_REMOTE_OPTS
        GLOBAL_TYPER_RESOLVED_REMOTE_OPTS = TyperResolvedRemoteOpts(
            environment=environment,
            node_username=node_username,
            node_password=node_password,
            ssh_private_key_file_path=ssh_private_key_file_path,
            ip_discovery_range=ip_discovery_range,
            remote_hosts=remote_hosts,
        )


GLOBAL_TYPER_RESOLVED_REMOTE_OPTS: TyperResolvedRemoteOpts = None


class CliRemoteOpts:

    environment: Optional[RunEnvironment]
    node_username: Optional[str]
    node_password: Optional[str]
    ssh_private_key_file_path: Optional[str]
    ip_discovery_range: Optional[str]

    # Calculated
    ansible_hosts: List[AnsibleHost]

    def __init__(
        self,
        environment: Optional[RunEnvironment] = None,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ssh_private_key_file_path: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
        remote_hosts: Optional[dict[str, RemoteConfig.Host]] = None,
    ) -> None:

        self.environment = environment
        self.node_username = node_username
        self.node_password = node_password
        self.ssh_private_key_file_path = ssh_private_key_file_path
        self.ip_discovery_range = ip_discovery_range
        self.ansible_hosts = self._to_ansible_hosts(remote_hosts)

    @staticmethod
    def maybe_get() -> "CliRemoteOpts":
        if GLOBAL_TYPER_RESOLVED_REMOTE_OPTS:
            return CliRemoteOpts(
                environment=GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._environment,
                node_username=GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._node_username,
                node_password=GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._node_password,
                ssh_private_key_file_path=GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._ssh_private_key_file_path,
                ip_discovery_range=GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._ip_discovery_range,
                remote_hosts=GLOBAL_TYPER_RESOLVED_REMOTE_OPTS._remote_hosts,
            )
        return None

    def _to_ansible_hosts(self, hosts: dict[str, RemoteConfig.Host]) -> List[AnsibleHost]:
        if not hosts:
            return None
        result: List[AnsibleHost] = []
        for key, value in hosts.items():
            # If user supplied remote options via CLI arguments - override all other sources
            result.append(
                AnsibleHost(
                    host=value.name,
                    ip_address=value.address,
                    username=self.node_username if self.node_username else value.auth.username,
                    password=self.node_password if self.node_password else value.auth.password,
                    ssh_private_key_file_path=self.ssh_private_key_file_path
                    if self.ssh_private_key_file_path
                    else value.auth.ssh_private_key_file_path,
                )
            )
        return result

    def print(self) -> None:
        logger.debug(
            f"CliRemoteOpts: \n"
            + f"  environment: {self.environment}\n"
            + f"  node_username: {self.node_username}\n"
            + f"  node_password: {self.node_password}\n"
            + f"  ip_discovery_range: {self.ip_discovery_range}\n"
            + f"  ssh_private_key_file_path: {self.ssh_private_key_file_path}\n"
            + f"  ansible_hosts: {'supplied via CLI arguments or user config' if self.ansible_hosts is not None else None}\n"
        )
