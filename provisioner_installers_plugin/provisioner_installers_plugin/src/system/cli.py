#!/usr/bin/env python3


import click
from provisioner_installers_plugin.src.installer.cmd.installer_cmd import (
    UtilityInstallerCmd,
    UtilityInstallerCmdArgs,
)
from provisioner_installers_plugin.src.installer.domain.command import InstallerSubCommandName
from provisioner_installers_plugin.src.installer.domain.dynamic_args import DynamicArgs
from provisioner_installers_plugin.src.installer.domain.version import NameVersionArgsTuple

from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.menu_format import CustomGroup
from provisioner_shared.components.runtime.cli.modifiers import CliModifiers
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator


def register_system_commands(cli_group: click.Group):

    @cli_group.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_modifiers
    @click.pass_context
    def system(ctx: click.Context):
        """Select a system app to install on any OS/Architecture"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @system.command()
    @click.option(
        "--version",
        show_default=False,
        help="Python version",
        envvar="PROV_SYSTEM_PYTHON_VER",
    )
    @cli_modifiers
    @click.pass_context
    def python(ctx: click.Context, version: str):
        """
        Install Python / pip package manager
        """
        python_install(
            name_ver=NameVersionArgsTuple("python", version, DynamicArgs({})),
            modifiers=CliModifiers.from_click_ctx(ctx),
            remote_opts=RemoteOpts.from_click_ctx(ctx),
        )


def python_install(name_ver: NameVersionArgsTuple, modifiers: CliModifiers, remote_opts: RemoteOpts) -> None:
    cli_ctx = CliContextManager.create(modifiers)
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="python",
        call=lambda: UtilityInstallerCmd().run(
            ctx=cli_ctx,
            args=UtilityInstallerCmdArgs(
                utils_to_install=[name_ver],
                sub_command_name=InstallerSubCommandName.System,
                remote_opts=remote_opts,
            ),
        ),
        verbose=cli_ctx.is_verbose(),
    )
