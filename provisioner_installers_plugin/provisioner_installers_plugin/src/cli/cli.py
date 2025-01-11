#!/usr/bin/env python3

import typer
from provisioner_installers_plugin.src.installer.cmd.installer_cmd import (
    UtilityInstallerCmd,
    UtilityInstallerCmdArgs,
)
from provisioner_installers_plugin.src.installer.domain.command import InstallerSubCommandName

from provisioner_shared.components.remote.remote_opts import TyperRemoteOpts
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator

cli_apps = typer.Typer()

typer_remote_opts: TyperRemoteOpts = None


def register_cli_commands(app: typer.Typer, remote_opts: TyperRemoteOpts):
    global typer_remote_opts
    typer_remote_opts = remote_opts

    cli_apps.command("anchor")(anchor)
    cli_apps.command("helm")(helm)
    # cli_apps.command("test")(k3s_server)
    # cli_apps.command("docker")(k3s_server)

    app.add_typer(
        cli_apps,
        name="cli",
        invoke_without_command=True,
        no_args_is_help=True,
        help="Select a CLI utility to install on any OS/Architecture",
    )


def anchor() -> None:
    """
    Create Dynamic CLI's as your GitOps Marketplace
    """
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="anchor",
        call=lambda: UtilityInstallerCmd().run(
            ctx=CliContextManager.create(),
            args=UtilityInstallerCmdArgs(
                utilities=["anchor"],
                sub_command_name=InstallerSubCommandName.CLI,
                remote_opts=typer_remote_opts.to_cli_opts(),
            ),
        ),
    )


def helm() -> None:
    """
    Package Manager for Kubernetes
    """
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="helm",
        call=lambda: UtilityInstallerCmd().run(
            ctx=CliContextManager.create(),
            args=UtilityInstallerCmdArgs(
                utilities=["helm"],
                sub_command_name=InstallerSubCommandName.CLI,
                remote_opts=typer_remote_opts.to_cli_opts(),
            ),
        ),
    )
