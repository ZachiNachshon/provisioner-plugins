#!/usr/bin/env python3


import click
from provisioner_installers_plugin.src.installer.cmd.installer_cmd import UtilityInstallerCmd, UtilityInstallerCmdArgs
from provisioner_installers_plugin.src.installer.domain.command import InstallerSubCommandName
from provisioner_installers_plugin.src.utilities.utilities_versions import ToolingVersions

from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.menu_format import CustomGroup
from provisioner_shared.components.runtime.cli.modifiers import CliModifiers
from provisioner_shared.components.runtime.cli.version import NameVersionTuple
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator

# Fully compliant lightweight Kubernetes distribution (https://k3s.io)


def register_k3s_commands(cli_group: click.Group):

    @cli_group.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_modifiers
    @click.pass_context
    def k8s(ctx: click.Context):
        """Kubernetes based installables"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @k8s.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_modifiers
    @click.pass_context
    def distro(ctx: click.Context):
        """Kubernetes distributions"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @distro.command()
    @click.option(
        "--k3s-token",
        show_default=False,
        help="k3s server token",
        envvar="PROV_K3S_TOKEN",
    )
    @click.option(
        "--k3s-args",
        default="--disable traefik --disable kubernetes-dashboard",
        show_default=True,
        is_flag=False,
        help="Optional server configuration as CLI arguments",
        envvar="PROV_K3S_ADDITIONAL_CLI_ARGS",
    )
    @click.option(
        "--install-as-binary",
        default=False,
        is_flag=True,
        help="Install K3s server as a binary instead of system service",
        envvar="PROV_K3S_INSTALL_AS_BINARY",
    )
    @click.option(
        "--version",
        show_default=False,
        required=False,
        default=ToolingVersions.k3s_server_ver,
        help="K3s version",
        envvar="PROV_K3S_SERVER_VERSION",
    )
    @cli_modifiers
    @click.pass_context
    def k3s_server(ctx: click.Context, k3s_token: str, k3s_args: str, install_as_binary: bool, version: str):
        """
        Install a Rancher K3s Server as a service on systemd and openrc based systems
        """
        k3s_server_install(
            NameVersionTuple("k3s-server", version),
            k3s_token,
            k3s_args,
            install_as_binary,
            CliModifiers.from_click_ctx(ctx),
            RemoteOpts.from_click_ctx(ctx),
        )

    @distro.command()
    @click.option(
        "--k3s-url",
        show_default=False,
        help="K3s server address",
        envvar="PROV_K3S_URL",
    )
    @click.option(
        "--k3s-token",
        show_default=False,
        help="k3s server token",
        envvar="PROV_K3S_TOKEN",
    )
    @click.option(
        "--k3s-args",
        default="--disable traefik --disable kubernetes-dashboard",
        show_default=True,
        is_flag=False,
        help="Optional server configuration as CLI arguments",
        envvar="PROV_K3S_ADDITIONAL_CLI_ARGS",
    )
    @click.option(
        "--install-as-binary",
        default=False,
        is_flag=True,
        help="Install K3s agent as a binary instead of system service",
        envvar="INSTALL_AS_BINARY",
    )
    @click.option(
        "--version",
        show_default=False,
        required=False,
        default=ToolingVersions.k3s_agent_ver,
        help="K3s version",
        envvar="PROV_K3S_AGENT_VERSION",
    )
    @cli_modifiers
    @click.pass_context
    def k3s_agent(
        ctx: click.Context, k3s_token: str, k3s_url: str, k3s_args: str, install_as_binary: bool, version: str
    ):
        """
        Install a Rancher K3s Agent as a service on systemd and openrc based systems
        """
        k3s_agent_install(
            NameVersionTuple("k3s-server", version),
            k3s_token,
            k3s_url,
            k3s_args,
            install_as_binary,
            CliModifiers.from_click_ctx(ctx),
            RemoteOpts.from_click_ctx(ctx),
        )


def k3s_server_install(
    name_ver: NameVersionTuple,
    k3s_token: str,
    k3s_args: str,
    install_as_binary: bool,
    modifiers: CliModifiers,
    remote_opts: RemoteOpts,
) -> None:
    cli_ctx = CliContextManager.create(modifiers)
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="k3s-server",
        call=lambda: UtilityInstallerCmd().run(
            ctx=cli_ctx,
            args=UtilityInstallerCmdArgs(
                utils_to_install=[name_ver],
                sub_command_name=InstallerSubCommandName.K8S,
                dynamic_args={
                    "k3s_token": k3s_token,
                    "k3s_additional_cli_args": k3s_args,
                    "k3s_install_as_binary": install_as_binary,
                    "k3s_version": name_ver.version,
                },
                remote_opts=remote_opts,
            ),
        ),
        verbose=cli_ctx.is_verbose(),
    )


def k3s_agent_install(
    name_ver: NameVersionTuple,
    k3s_token: str,
    k3s_url: str,
    k3s_args: str,
    install_as_binary: bool,
    modifiers: CliModifiers,
    remote_opts: RemoteOpts,
) -> None:
    cli_ctx = CliContextManager.create(modifiers)
    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="k3s-agent",
        call=lambda: UtilityInstallerCmd().run(
            ctx=cli_ctx,
            args=UtilityInstallerCmdArgs(
                utils_to_install=[name_ver],
                sub_command_name=InstallerSubCommandName.K8S,
                dynamic_args={
                    "k3s_token": k3s_token,
                    "k3s_url": k3s_url,
                    "k3s_additional_cli_args": k3s_args,
                    "k3s_install_as_binary": install_as_binary,
                    "k3s_version": name_ver.version,
                },
                remote_opts=remote_opts,
            ),
        ),
        verbose=cli_ctx.is_verbose(),
    )
