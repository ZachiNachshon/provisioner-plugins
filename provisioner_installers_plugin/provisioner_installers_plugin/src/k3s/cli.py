#!/usr/bin/env python3


from typing import Optional

import click
from provisioner_installers_plugin.src.installer.cmd.installer_cmd import (
    UtilityInstallerCmd,
    UtilityInstallerCmdArgs,
)
from provisioner_installers_plugin.src.installer.domain.command import InstallerSubCommandName

from plugins.provisioner_installers_plugin.provisioner_installers_plugin.src.config.domain.config import (
    InstallersConfig,
)
from provisioner_shared.components.remote.cli_remote_opts import cli_remote_opts
from provisioner_shared.components.remote.domain.config import RemoteConfig
from provisioner_shared.components.remote.remote_opts import CliRemoteOpts
from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.menu_format import CustomGroup
from provisioner_shared.components.runtime.cli.modifiers import CliModifiers
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator


def register_k3s_commands(
    cli_group: click.Group,
    installers_cfg: Optional[InstallersConfig] = None,
):

    @cli_group.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_remote_opts(remote_config=installers_cfg.remote if installers_cfg is not None else RemoteConfig())
    @cli_modifiers
    @click.pass_context
    def k3s(ctx: click.Context):
        """Fully compliant lightweight Kubernetes distribution (https://k3s.io)"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @k3s.command()
    @click.option(
        "--k3s-token",
        show_default=False,
        help="k3s server token",
        envvar="K3S_TOKEN",
    )
    @click.option(
        "--k3s-args",
        default="--disable traefik --disable kubernetes-dashboard",
        show_default=True,
        is_flag=False,
        help="Optional server configuration as CLI arguments",
        envvar="ADDITIONAL_CLI_ARGS",
    )
    @click.option(
        "--install-as-binary",
        default=False,
        is_flag=True,
        help="Install K3s server as a binary instead of system service",
        envvar="INSTALL_AS_BINARY",
    )
    @cli_modifiers
    @click.pass_context
    def k3s_server(ctx: click.Context, k3s_token: str, k3s_args: str, install_as_binary: bool):
        """
        Install a Rancher K3s Server as a service on systemd and openrc based systems
        """
        k3s_server_install(
            k3s_token, k3s_args, install_as_binary, CliModifiers.from_click_ctx(ctx), CliRemoteOpts.from_click_ctx(ctx)
        )

    @k3s.command()
    @click.option(
        "--k3s-token",
        show_default=False,
        help="k3s server token",
        envvar="K3S_TOKEN",
    )
    @click.option(
        "--k3s-url",
        show_default=False,
        help="K3s server address",
        envvar="K3S_URL",
    )
    @click.option(
        "--k3s-args",
        default="--disable traefik --disable kubernetes-dashboard",
        show_default=True,
        is_flag=False,
        help="Optional server configuration as CLI arguments",
        envvar="ADDITIONAL_CLI_ARGS",
    )
    @click.option(
        "--install-as-binary",
        default=False,
        is_flag=True,
        help="Install K3s agent as a binary instead of system service",
        envvar="INSTALL_AS_BINARY",
    )
    @cli_modifiers
    @click.pass_context
    def k3s_agent(ctx: click.Context, k3s_token: str, k3s_url: str, k3s_args: str, install_as_binary: bool):
        """
        Install a Rancher K3s Agent as a service on systemd and openrc based systems
        """
        k3s_agent_install(
            k3s_token,
            k3s_url,
            k3s_args,
            install_as_binary,
            CliModifiers.from_click_ctx(ctx),
            CliRemoteOpts.from_click_ctx(ctx),
        )


def k3s_server_install(
    k3s_token: str, k3s_args: str, install_as_binary: bool, modifiers: CliModifiers, remote_opts: CliRemoteOpts
) -> None:
    cli_ctx = CliContextManager.create(modifiers)
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="k3s-server",
        call=lambda: UtilityInstallerCmd().run(
            ctx=cli_ctx,
            args=UtilityInstallerCmdArgs(
                utilities=["k3s-server"],
                sub_command_name=InstallerSubCommandName.K3S,
                dynamic_args={
                    "k3s_token": k3s_token,
                    "k3s_additional_cli_args": k3s_args,
                    "k3s_install_as_binary": install_as_binary,
                },
                remote_opts=remote_opts,
            ),
        ),
        verbose=cli_ctx.is_verbose(),
    )


def k3s_agent_install(
    k3s_token: str,
    k3s_url: str,
    k3s_args: str,
    install_as_binary: bool,
    modifiers: CliModifiers,
    remote_opts: CliRemoteOpts,
) -> None:
    cli_ctx = CliContextManager.create(modifiers)
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="k3s-agent",
        call=lambda: UtilityInstallerCmd().run(
            ctx=cli_ctx,
            args=UtilityInstallerCmdArgs(
                utilities=["k3s-agent"],
                sub_command_name=InstallerSubCommandName.K3S,
                dynamic_args={
                    "k3s_token": k3s_token,
                    "k3s_url": k3s_url,
                    "k3s_additional_cli_args": k3s_args,
                    "k3s_install_as_binary": install_as_binary,
                },
                remote_opts=remote_opts,
            ),
        ),
        verbose=cli_ctx.is_verbose(),
    )
