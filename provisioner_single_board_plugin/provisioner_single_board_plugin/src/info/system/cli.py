#!/usr/bin/env python3

from typing import Optional

import click
from provisioner_single_board_plugin.src.config.domain.config import SingleBoardConfig
from provisioner_single_board_plugin.src.info.system.system_info_cmd import SystemInfoCmd, SystemInfoCmdArgs

from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.modifiers import CliModifiers
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator


def register_system_info_commands(cli_group: click.Group, single_board_cfg: Optional[SingleBoardConfig] = None):

    @cli_group.command()
    @cli_modifiers
    @click.pass_context
    def collect(ctx: click.Context) -> None:
        """
        Collect system information from a remote host
        """
        cli_ctx = CliContextManager.create(modifiers=CliModifiers.from_click_ctx(ctx))
        remote_opts = RemoteOpts.from_click_ctx(ctx)
        Evaluator.eval_cli_entrypoint_step(
            name="System Info Collect",
            call=lambda: SystemInfoCmd().run(ctx=cli_ctx, args=SystemInfoCmdArgs(remote_opts=remote_opts)),
            error_message="Failed to collect system information",
            verbose=cli_ctx.is_verbose(),
        )
