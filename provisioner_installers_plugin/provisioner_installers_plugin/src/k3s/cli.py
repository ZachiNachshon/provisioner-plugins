#!/usr/bin/env python3


import click
from provisioner_installers_plugin.src.installer.cmd.installer_cmd import UtilityInstallerCmd, UtilityInstallerCmdArgs
from provisioner_installers_plugin.src.installer.domain.command import InstallerSubCommandName
from provisioner_installers_plugin.src.installer.domain.dynamic_args import DynamicArgs
from provisioner_installers_plugin.src.installer.domain.version import NameVersionArgsTuple
from provisioner_installers_plugin.src.k3s.cmd.k3s_download_kubeconfig import (
    K3sKubeConfigDownloadCmd,
    K3sKubeConfigDownloadCmdArgs,
)
from provisioner_installers_plugin.src.k3s.cmd.k3s_gather_info_cmd import K3sGatherInfoCmd, K3sGatherInfoCmdArgs
from provisioner_installers_plugin.src.utilities.utilities_versions import ToolingVersions

from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.menu_format import CustomGroup
from provisioner_shared.components.runtime.cli.modifiers import CliModifiers
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
        required=False,
        help="K3s server token in format K10<CA-HASH>::<USERNAME>:<PASSWORD> or plaintext password",
        envvar="PROV_K3S_SERVER_TOKEN",
    )
    @click.option(
        "--k3s-args",
        default="--disable=traefik,kubernetes-dashboard",
        show_default=True,
        is_flag=False,
        help="Optional server configuration as CLI arguments",
        envvar="PROV_K3S_SERVER_ADDITIONAL_CLI_ARGS",
    )
    @click.option(
        "--install-as-binary",
        default=False,
        is_flag=True,
        help="Install K3s server as a binary instead of system service",
        envvar="PROV_K3S_SERVER_INSTALL_AS_BINARY",
    )
    @click.option(
        "--use-kube-config",
        default=False,
        is_flag=True,
        help="Write kubeconfig to ~/.kube/config instead of the default /etc/rancher/k3s/k3s.yaml",
        envvar="PROV_K3S_SERVER_USE_KUBE_CONFIG",
    )
    @click.option(
        "--uninstall",
        default=False,
        is_flag=True,
        help="Uninstall K3s server instead of installing it",
        envvar="PROV_K3S_SERVER_UNINSTALL",
    )
    @click.option(
        "--version",
        show_default=True,
        required=False,
        default=ToolingVersions.k3s_server_ver,
        help="K3s version",
        envvar="PROV_K3S_SERVER_VERSION",
    )
    @cli_modifiers
    @click.pass_context
    def k3s_server(
        ctx: click.Context,
        k3s_token: str,
        k3s_args: str,
        install_as_binary: bool,
        use_kube_config: bool,
        uninstall: bool,
        version: str,
    ):
        """
        Install or uninstall a Rancher K3s Server on systemd and openrc based systems
        """
        k3s_server_install(
            NameVersionArgsTuple(
                "k3s-server",
                version,
                DynamicArgs(
                    {
                        "k3s-token": k3s_token,
                        "k3s-args": f'"{k3s_args}"' if k3s_args else "",
                        "install-as-binary": install_as_binary,
                        "use-kube-config": use_kube_config,
                        "uninstall": uninstall,
                    }
                ),
            ),
            CliModifiers.from_click_ctx(ctx),
            RemoteOpts.from_click_ctx(ctx),
        )

    @distro.command()
    @click.option(
        "--k3s-url",
        show_default=False,
        required=False,
        help="K3s server address",
        envvar="PROV_K3S_AGENT_SERVER_URL",
    )
    @click.option(
        "--k3s-token",
        show_default=False,
        required=False,
        help="k3s server token",
        envvar="PROV_K3S_AGENT_TOKEN",
    )
    @click.option(
        "--k3s-args",
        is_flag=False,
        help="Optional server configuration as CLI arguments",
        envvar="PROV_K3S_AGENT_ADDITIONAL_CLI_ARGS",
    )
    @click.option(
        "--install-as-binary",
        default=False,
        is_flag=True,
        help="Install K3s agent as a binary instead of system service",
        envvar="PROV_K3S_AGENT_INSTALL_AS_BINARY",
    )
    @click.option(
        "--uninstall",
        default=False,
        is_flag=True,
        help="Uninstall K3s agent instead of installing it",
        envvar="PROV_K3S_AGENT_UNINSTALL",
    )
    @click.option(
        "--version",
        show_default=True,
        required=False,
        default=ToolingVersions.k3s_agent_ver,
        help="K3s version",
        envvar="PROV_K3S_AGENT_VERSION",
    )
    @cli_modifiers
    @click.pass_context
    def k3s_agent(
        ctx: click.Context,
        k3s_token: str,
        k3s_url: str,
        k3s_args: str,
        install_as_binary: bool,
        uninstall: bool,
        version: str,
    ):
        """
        Install or uninstall a Rancher K3s Agent on systemd and openrc based systems
        """
        if not uninstall:
            if not k3s_token:
                raise click.UsageError("--k3s-token is required for installation")
            if not k3s_url:
                raise click.UsageError("--k3s-url is required for installation")

        k3s_agent_install(
            NameVersionArgsTuple(
                "k3s-agent",
                version,
                DynamicArgs(
                    {
                        "k3s-url": k3s_url,
                        "k3s-token": k3s_token,
                        "k3s-args": f'"{k3s_args}"' if k3s_args else "",
                        "install-as-binary": install_as_binary,
                        "uninstall": uninstall,
                    }
                ),
            ),
            CliModifiers.from_click_ctx(ctx),
            RemoteOpts.from_click_ctx(ctx),
        )

    @distro.command()
    @cli_modifiers
    @click.pass_context
    def k3s_info(ctx: click.Context):
        """
        Gather and display K3s configuration information from a remote host
        """
        k3s_info_gather(
            modifiers=CliModifiers.from_click_ctx(ctx),
            remote_opts=RemoteOpts.from_click_ctx(ctx),
        )

    @click.option(
        "--server-url",
        show_default=True,
        required=False,
        default="https://kmaster:6443",
        help="K3s server URL",
        envvar="PROV_K3S_KUBECONFIG_SERVER_URL",
    )
    @click.option(
        "--dest",
        show_default=True,
        required=False,
        default="~/.kube/k3s/config",
        help="Destination file path for the kubeconfig file",
        envvar="PROV_K3S_KUBECONFIG_DESTINATION",
    )
    @distro.command()
    @cli_modifiers
    @click.pass_context
    def k3s_kubeconfig(ctx: click.Context, dest: str, server_url: str):
        """
        Download K3s kubeconfig from a remote server
        """
        k3s_kubeconfig_download(
            modifiers=CliModifiers.from_click_ctx(ctx),
            remote_opts=RemoteOpts.from_click_ctx(ctx),
            dest_file_path=dest,
            server_url=server_url,
        )


def k3s_server_install(
    name_ver_args: NameVersionArgsTuple,
    modifiers: CliModifiers,
    remote_opts: RemoteOpts,
) -> None:
    cli_ctx = CliContextManager.create(modifiers)
    # Extract uninstall flag from args if present
    uninstall = False
    if name_ver_args.maybe_args and "uninstall" in name_ver_args.maybe_args.as_dict():
        uninstall = name_ver_args.maybe_args.as_dict()["uninstall"]

    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="k3s-server",
        call=lambda: UtilityInstallerCmd().run(
            ctx=cli_ctx,
            args=UtilityInstallerCmdArgs(
                utils_to_install=[name_ver_args],
                sub_command_name=InstallerSubCommandName.K8S,
                remote_opts=remote_opts,
                uninstall=uninstall,
            ),
        ),
        verbose=cli_ctx.is_verbose(),
    )


def k3s_agent_install(
    name_ver_args: NameVersionArgsTuple,
    modifiers: CliModifiers,
    remote_opts: RemoteOpts,
) -> None:
    cli_ctx = CliContextManager.create(modifiers)
    # Extract uninstall flag from args if present
    uninstall = False
    if name_ver_args.maybe_args and "uninstall" in name_ver_args.maybe_args.as_dict():
        uninstall = name_ver_args.maybe_args.as_dict()["uninstall"]

    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="k3s-agent",
        call=lambda: UtilityInstallerCmd().run(
            ctx=cli_ctx,
            args=UtilityInstallerCmdArgs(
                utils_to_install=[name_ver_args],
                sub_command_name=InstallerSubCommandName.K8S,
                remote_opts=remote_opts,
                uninstall=uninstall,
            ),
        ),
        verbose=cli_ctx.is_verbose(),
    )


def k3s_info_gather(modifiers: CliModifiers, remote_opts: RemoteOpts) -> None:
    cli_ctx = CliContextManager.create(modifiers)

    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="k3s-info",
        call=lambda: K3sGatherInfoCmd().run(
            ctx=cli_ctx,
            args=K3sGatherInfoCmdArgs(
                remote_opts=remote_opts,
            ),
        ),
        verbose=cli_ctx.is_verbose(),
    )


def k3s_kubeconfig_download(
    modifiers: CliModifiers, remote_opts: RemoteOpts, dest_file_path: str, server_url: str
) -> None:
    cli_ctx = CliContextManager.create(modifiers)

    Evaluator.eval_installer_cli_entrypoint_pyfn_step(
        name="k3s-kubeconfig",
        call=lambda: K3sKubeConfigDownloadCmd().run(
            ctx=cli_ctx,
            args=K3sKubeConfigDownloadCmdArgs(
                remote_opts=remote_opts,
                dest_file_path=dest_file_path,
                server_url=server_url,
            ),
        ),
        verbose=cli_ctx.is_verbose(),
    )
