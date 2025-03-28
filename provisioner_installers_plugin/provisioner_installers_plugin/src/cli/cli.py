#!/usr/bin/env python3

from typing import List

import click
from provisioner_installers_plugin.src.installer.cmd.installer_cmd import UtilityInstallerCmd, UtilityInstallerCmdArgs
from provisioner_installers_plugin.src.installer.cmd.list_cmd import UtilityListCmd
from provisioner_installers_plugin.src.installer.domain.command import InstallerSubCommandName

from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.modifiers import CliModifiers
from provisioner_shared.components.runtime.cli.version import NameVersionTuple, try_extract_name_version_tuple
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator


def register_cli_commands(cli_group: click.Group):

    @cli_group.command()
    @cli_modifiers
    @click.argument("args", nargs=-1)
    @click.pass_context
    def cli(ctx: click.Context, args: str):
        """Select a CLI utility to install on any OS/Architecture"""
        if args:
            to_install: List[NameVersionTuple] = []
            for name in args:
                name_ver = try_extract_name_version_tuple(name)
                to_install.append(name_ver)
            install_utilities(
                to_install, modifiers=CliModifiers.from_click_ctx(ctx), remote_opts=RemoteOpts.from_click_ctx(ctx)
            )
        else:
            list_utilities(modifiers=CliModifiers.from_click_ctx(ctx))


def install_utilities(utils_name_ver: List[NameVersionTuple], modifiers: CliModifiers, remote_opts: RemoteOpts) -> None:
    cli_ctx = CliContextManager.create(modifiers)
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="Install Utility Command",
        call=lambda: UtilityInstallerCmd().run(
            ctx=cli_ctx,
            args=UtilityInstallerCmdArgs(
                utils_to_install=utils_name_ver,
                sub_command_name=InstallerSubCommandName.CLI,
                remote_opts=remote_opts,
            ),
        ),
        verbose=cli_ctx.is_verbose(),
    )


def list_utilities(modifiers: CliModifiers) -> None:
    cli_ctx = CliContextManager.create(modifiers)
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="list_utilities",
        call=lambda: UtilityListCmd().run(ctx=cli_ctx),
        verbose=cli_ctx.is_verbose(),
    )
