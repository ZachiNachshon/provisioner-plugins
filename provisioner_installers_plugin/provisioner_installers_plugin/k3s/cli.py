#!/usr/bin/env python3


from typing import Optional

import typer
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.infra.context import CliContextManager
from python_core_lib.infra.evaluator import Evaluator

from provisioner_installers_plugin.installer.cmd.installer_cmd import (
    UtilityInstallerCmd,
    UtilityInstallerCmdArgs,
)
from provisioner_installers_plugin.installer.domain.command import InstallerSubCommandName

# from provisioner_installers_plugin.cli.k3s.cli import register_command


def register_k3s_commands(app: typer.Typer, callback_remote_args):
    k8s_apps = typer.Typer()

    k8s_apps.command("server")(k3s_server)
    k8s_apps.command("agent")(k3s_agent)

    # register_command(cli_apps)
    app.add_typer(
        k8s_apps,
        name="k3s",
        invoke_without_command=True,
        no_args_is_help=True,
        help="Fully compliant lightweight Kubernetes distribution (https://k3s.io)",
        callback=callback_remote_args,
    )


def k3s_server(
    k3s_token: str = typer.Argument(..., show_default=False, envvar="K3S_TOKEN", help="k3s server token"),
    install_as_service: Optional[bool] = typer.Option(
        False,
        "--install-as-service",
        envvar="INSTALL_AS_SERVICE",
        is_flag=True,
        help="Install K3s as a service on systemd and openrc based systems",
    ),
) -> None:
    """
    Install a Rancher K3s Server
    """
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="k3s-server",
        call=lambda: UtilityInstallerCmd().run(
            ctx=CliContextManager.create(),
            args=UtilityInstallerCmdArgs(
                utilities=["k3s-server"],
                sub_command_name=InstallerSubCommandName.K3S,
                dynamic_args={"k3s_token": k3s_token, "install_as_service": install_as_service},
                remote_opts=CliRemoteOpts.maybe_get(),
            ),
        ),
    )


def k3s_agent(
    k3s_token: str = typer.Argument(..., show_default=False, envvar="K3S_TOKEN", help="k3s server token"),
    k3s_url: str = typer.Argument(..., show_default=False, envvar="K3S_URL", help="K3s server address"),
    install_as_service: Optional[bool] = typer.Option(
        False,
        "--install-as-service",
        envvar="INSTALL_AS_SERVICE",
        is_flag=True,
        help="Install K3s as a service on systemd and openrc based systems",
    ),
) -> None:
    """
    Install a Rancher K3s Agent
    """
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="k3s-agent",
        call=lambda: UtilityInstallerCmd().run(
            ctx=CliContextManager.create(),
            args=UtilityInstallerCmdArgs(
                utilities=["k3s-agent"],
                sub_command_name=InstallerSubCommandName.K3S,
                dynamic_args={"k3s_token": k3s_token, "k3s_url": k3s_url, "install_as_service": install_as_service},
                remote_opts=CliRemoteOpts.maybe_get(),
            ),
        ),
    )
