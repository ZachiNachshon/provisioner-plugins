#!/usr/bin/env python3

import typer

from .domain.config import RemoteConfig

class TyperRemoteOpts:
    """
    Load method MUST be called to populate the config object
    """

    # Static variable
    remote_config: RemoteConfig

    @staticmethod
    def load(remote_config: RemoteConfig) -> None:
        TyperRemoteOpts.remote_config = remote_config

    def node_username():
        return typer.Option(
            TyperRemoteOpts.remote_config.auth.node_username,
            help="(Remote only) Remote node username",
            envvar="NODE_USERNAME",
        )

    def node_password():
        return typer.Option(
            TyperRemoteOpts.remote_config.auth.node_password,
            help="(Remote only) Remote node password",
            envvar="NODE_PASSWORD",
        )

    def ssh_private_key_file_path():
        return typer.Option(
            TyperRemoteOpts.remote_config.auth.ssh_private_key_file_path,
            show_default=False,
            help="(Remote only) Remote SSH private key file path",
            envvar="SSH_PRIVATE_KEY_FILE_PATH",
        )

    def ip_discovery_range():
        return typer.Option(
            TyperRemoteOpts.remote_config.lan_scan.ip_discovery_range,
            help="(Remote only) LAN network IP discovery range",
            envvar="IP_DISCOVERY_RANGE",
        )
