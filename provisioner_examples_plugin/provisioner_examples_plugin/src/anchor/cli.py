#!/usr/bin/env python3

from typing import Optional

import click

from provisioner_examples_plugin.src.anchor.anchor_cmd import AnchorCmd, AnchorCmdArgs
from provisioner_shared.components.remote.cli_remote_opts import cli_remote_opts
from provisioner_shared.components.remote.domain.config import RemoteConfig
from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.menu_format import CustomGroup
from provisioner_shared.components.runtime.cli.modifiers import CliModifiers
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator
from provisioner_shared.components.vcs.cli_vcs_opts import cli_vcs_opts
from provisioner_shared.components.vcs.domain.config import VersionControlConfig
from provisioner_shared.components.vcs.vcs_opts import CliVersionControlOpts


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
    def run_cmd(ctx: click.Context, run_command: str):
        """
        Run a dummy anchor run scenario locally or on remote machine via Ansible playbook
        """
        cli_ctx = CliContextManager.create(modifiers=CliModifiers.from_click_ctx(ctx))
        Evaluator.eval_cli_entrypoint_step(
            name="Run Anchor Command",
            call=lambda: AnchorCmd().run(
                ctx=cli_ctx,
                args=AnchorCmdArgs(
                    anchor_run_command=run_command,
                    vcs_opts=CliVersionControlOpts.from_click_ctx(ctx),
                    remote_opts=RemoteOpts.from_click_ctx(ctx),
                ),
            ),
            error_message="Failed to run anchor command",
            verbose=cli_ctx.is_verbose(),
        )
