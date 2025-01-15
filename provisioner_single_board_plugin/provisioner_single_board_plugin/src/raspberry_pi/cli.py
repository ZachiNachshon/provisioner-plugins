#!/usr/bin/env python3


from typing import Optional

import click

from plugins.provisioner_single_board_plugin.provisioner_single_board_plugin.src.config.domain.config import (
    SingleBoardConfig,
)
from plugins.provisioner_single_board_plugin.provisioner_single_board_plugin.src.raspberry_pi.node.cli import (
    register_node_commands,
)
from plugins.provisioner_single_board_plugin.provisioner_single_board_plugin.src.raspberry_pi.os.cli import (
    register_os_commands,
)
from provisioner_shared.components.remote.cli_remote_opts import cli_remote_opts
from provisioner_shared.components.remote.domain.config import RemoteConfig
from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.menu_format import CustomGroup


def register_raspberry_pi_commands(cli_group: click.Group, single_board_cfg: Optional[SingleBoardConfig] = None):

    @cli_group.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_modifiers
    @click.pass_context
    def raspberry_pi(ctx: click.Context):
        """Static IP address to set as the remote host IP address"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @raspberry_pi.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_remote_opts(remote_config=single_board_cfg.remote if single_board_cfg is not None else RemoteConfig())
    @cli_modifiers
    @click.pass_context
    def node(ctx: click.Context):
        """Raspbian node management for Raspberry Pi nodes"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @raspberry_pi.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_modifiers
    @click.pass_context
    def os(ctx: click.Context):
        """Raspbian OS management for Raspberry Pi nodes"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    register_node_commands(cli_group=node)
    register_os_commands(cli_group=os, single_board_cfg=single_board_cfg)
