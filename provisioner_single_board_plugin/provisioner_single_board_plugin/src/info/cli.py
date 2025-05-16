#!/usr/bin/env python3


from typing import Optional

import click
from provisioner_single_board_plugin.src.config.domain.config import (
    SingleBoardConfig,
)
from provisioner_single_board_plugin.src.info.system.cli import register_system_info_commands

from provisioner_shared.components.remote.cli_remote_opts import cli_remote_opts
from provisioner_shared.components.remote.domain.config import RemoteConfig
from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.menu_format import CustomGroup


def register_remote_info_commands(cli_group: click.Group, single_board_cfg: Optional[SingleBoardConfig] = None):

    @cli_group.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_remote_opts(remote_config=single_board_cfg.remote if single_board_cfg is not None else RemoteConfig())
    @cli_modifiers
    @click.pass_context
    def info(ctx: click.Context):
        """Read remote host information"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    register_system_info_commands(cli_group=info, single_board_cfg=single_board_cfg)
