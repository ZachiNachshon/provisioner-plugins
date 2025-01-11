#!/usr/bin/env python3


from typing import Optional

import typer
from provisioner_installers_plugin.src.installer.cmd.installer_cmd import (
    UtilityInstallerCmd,
    UtilityInstallerCmdArgs,
)
from provisioner_installers_plugin.src.installer.domain.command import InstallerSubCommandName

from provisioner_shared.components.remote.remote_opts import TyperRemoteOpts
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator

# from provisioner_installers_plugin.src.cli.k3s.cli import register_command

typer_remote_opts: TyperRemoteOpts = None


def register_k3s_commands(app: typer.Typer, remote_opts: TyperRemoteOpts):
    global typer_remote_opts
    typer_remote_opts = remote_opts

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
    )


def k3s_server(
    k3s_token: str = typer.Option(..., show_default=False, envvar="K3S_TOKEN", help="k3s server token"),
    additional_cli_args: Optional[str] = typer.Option(
        "--disable traefik --disable kubernetes-dashboard",
        envvar="ADDITIONAL_CLI_ARGS",
        is_flag=False,
        help="Optional server configuration as CLI arguments",
    ),
    install_as_binary: Optional[bool] = typer.Option(
        False,
        "--install-as-binary",
        envvar="INSTALL_AS_BINARY",
        is_flag=True,
        help="Install K3s server as a binary instead of system service",
    ),
) -> None:
    """
    Install a Rancher K3s Server as a service on systemd and openrc based systems
    """
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="k3s-server",
        call=lambda: UtilityInstallerCmd().run(
            ctx=CliContextManager.create(),
            args=UtilityInstallerCmdArgs(
                utilities=["k3s-server"],
                sub_command_name=InstallerSubCommandName.K3S,
                dynamic_args={
                    "k3s_token": k3s_token,
                    "k3s_additional_cli_args": additional_cli_args,
                    "k3s_install_as_binary": install_as_binary,
                },
                remote_opts=typer_remote_opts.to_cli_opts(),
            ),
        ),
    )


def k3s_agent(
    k3s_token: str = typer.Option(..., show_default=False, envvar="K3S_TOKEN", help="k3s server token"),
    k3s_url: str = typer.Option(..., show_default=False, envvar="K3S_URL", help="K3s server address"),
    additional_cli_args: Optional[str] = typer.Option(
        None,
        envvar="ADDITIONAL_CLI_ARGS",
        is_flag=False,
        help="Optional server configuration as CLI arguments",
    ),
    install_as_binary: Optional[bool] = typer.Option(
        False,
        "--install-as-binary",
        envvar="INSTALL_AS_BINARY",
        is_flag=True,
        help="Install K3s agent as a binary instead of system service",
    ),
) -> None:
    """
    Install a Rancher K3s Agent as a service on systemd and openrc based systems
    """
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="k3s-agent",
        call=lambda: UtilityInstallerCmd().run(
            ctx=CliContextManager.create(),
            args=UtilityInstallerCmdArgs(
                utilities=["k3s-agent"],
                sub_command_name=InstallerSubCommandName.K3S,
                dynamic_args={
                    "k3s_token": k3s_token,
                    "k3s_url": k3s_url,
                    "k3s_additional_cli_args": additional_cli_args,
                    "k3s_install_as_binary": install_as_binary,
                },
                remote_opts=typer_remote_opts.to_cli_opts(),
            ),
        ),
    )
