#!/usr/bin/env python3

import typer
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.infra.context import CliContextManager
from python_core_lib.infra.evaluator import Evaluator

from provisioner_installers_plugin.installer.cmd.installer_cmd import (
    UtilityInstallerCmd,
    UtilityInstallerCmdArgs,
)
from provisioner_installers_plugin.installer.domain.command import InstallerSubCommandName

cli_apps = typer.Typer()


def register_cli_commands(app: typer.Typer, callback_remote_args):

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
        callback=callback_remote_args,
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
                remote_opts=CliRemoteOpts.maybe_get(),
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
                utilities=["helm"], sub_command_name=InstallerSubCommandName.CLI, remote_opts=CliRemoteOpts.maybe_get()
            ),
        ),
    )
