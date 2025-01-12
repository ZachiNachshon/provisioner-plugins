#!/usr/bin/env python3

from typing import Optional

import click
from components.remote.cli_remote_opts import cli_remote_opts
from components.remote.domain.config import RemoteConfig
from components.remote.remote_opts import CliRemoteOpts
from components.runtime.cli.cli_modifiers import cli_modifiers
from components.runtime.cli.menu_format import CustomGroup
from components.runtime.cli.modifiers import CliModifiers
from provisioner_installers_plugin.src.installer.cmd.installer_cmd import (
    UtilityInstallerCmd,
    UtilityInstallerCmdArgs,
)
from provisioner_installers_plugin.src.installer.domain.command import InstallerSubCommandName

from plugins.provisioner_installers_plugin.provisioner_installers_plugin.src.config.domain.config import (
    InstallersConfig,
)
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator


def register_cli_commands(
    cli_group: click.Group,
    installers_cfg: Optional[InstallersConfig] = None,
):

    @cli_group.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_remote_opts(remote_config=installers_cfg.remote if installers_cfg is not None else RemoteConfig())
    @cli_modifiers
    @click.pass_context
    def cli(ctx: click.Context):
        """Select a CLI utility to install on any OS/Architecture"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @cli.command()
    @cli_modifiers
    @click.pass_context
    def anchor(ctx: click.Context):
        """
        Create Dynamic CLI's as your GitOps Marketplace
        """
        anchor_install(modifiers=CliModifiers.from_click_ctx(ctx), remote_opts=CliRemoteOpts.from_click_ctx(ctx))

    @cli.command()
    @cli_modifiers
    @click.pass_context
    def helm(ctx: click.Context):
        """
        Package Manager for Kubernetes
        """
        helm_install(modifiers=CliModifiers.from_click_ctx(ctx), remote_opts=CliRemoteOpts.from_click_ctx(ctx))


def anchor_install(modifiers: CliModifiers, remote_opts: CliRemoteOpts) -> None:
    cli_ctx = CliContextManager.create(modifiers)
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="anchor",
        call=lambda: UtilityInstallerCmd().run(
            ctx=cli_ctx,
            args=UtilityInstallerCmdArgs(
                utilities=["anchor"],
                sub_command_name=InstallerSubCommandName.CLI,
                remote_opts=remote_opts,
            ),
        ),
        verbose=cli_ctx.is_verbose(),
    )


def helm_install(modifiers: CliModifiers, remote_opts: CliRemoteOpts) -> None:
    cli_ctx = CliContextManager.create(modifiers)
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="helm",
        call=lambda: UtilityInstallerCmd().run(
            ctx=cli_ctx,
            args=UtilityInstallerCmdArgs(
                utilities=["helm"],
                sub_command_name=InstallerSubCommandName.CLI,
                remote_opts=remote_opts,
            ),
        ),
        verbose=cli_ctx.is_verbose(),
    )
