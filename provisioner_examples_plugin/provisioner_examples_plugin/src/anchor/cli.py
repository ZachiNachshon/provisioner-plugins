#!/usr/bin/env python3

from typing import Optional

import click
from components.remote.cli_remote_opts import cli_remote_opts
from components.remote.domain.config import RemoteConfig
from components.remote.remote_opts import CliRemoteOpts
from components.runtime.cli.cli_modifiers import cli_modifiers
from components.runtime.cli.menu_format import CustomGroup
from components.vcs.cli_vcs_opts import cli_vcs_opts
from components.vcs.domain.config import VersionControlConfig
from components.vcs.vcs_opts import CliVersionControlOpts

from provisioner_examples_plugin.src.anchor.anchor_cmd import AnchorCmd, AnchorCmdArgs
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator


def register_anchor_commands(
    cli_group: click.Group,
    remote_config: Optional[RemoteConfig] = None,
    vcs_config: Optional[VersionControlConfig] = None,
):

    @cli_group.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_vcs_opts(vcs_config=vcs_config)
    @cli_remote_opts(remote_config=remote_config)
    @cli_modifiers
    @click.pass_context
    def anchor(ctx):
        """Anchor run command (without 'anchor' command)"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @anchor.command()
    @click.argument(
        "run-command",
        type=click.STRING,
        required=True,
    )
    @cli_modifiers
    @click.pass_context
    def run_command(ctx, run_command: str):
        """
        Run a dummy anchor run scenario locally or on remote machine via Ansible playbook
        """
        Evaluator.eval_cli_entrypoint_step(
            name="Run Anchor Command",
            call=lambda: AnchorCmd().run(
                ctx=CliContextManager.create(),
                args=AnchorCmdArgs(
                    anchor_run_command=run_command,
                    vcs_opts=CliVersionControlOpts.from_click_ctx(ctx),
                    remote_opts=CliRemoteOpts.from_click_ctx(ctx),
                ),
            ),
            error_message="Failed to run anchor command",
        )
