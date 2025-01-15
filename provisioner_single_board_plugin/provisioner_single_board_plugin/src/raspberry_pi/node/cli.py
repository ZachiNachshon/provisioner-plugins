#!/usr/bin/env python3

from typing import Optional

import click
from provisioner_single_board_plugin.src.raspberry_pi.node.configure_cmd import RPiOsConfigureCmd, RPiOsConfigureCmdArgs
from provisioner_single_board_plugin.src.raspberry_pi.node.network_cmd import (
    RPiNetworkConfigureCmd,
    RPiNetworkConfigureCmdArgs,
)

from provisioner_shared.components.remote.remote_opts import CliRemoteOpts
from provisioner_shared.components.runtime.cli.modifiers import CliModifiers
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator


def register_node_commands(cli_group: click.Group):

    @cli_group.command()
    @click.pass_context
    def configure(ctx: click.Context) -> None:
        """
        Select a remote Raspberry Pi node to configure Raspbian OS software and hardware settings.
        Configuration is aimed for an optimal headless Raspberry Pi used as a Kubernetes cluster node.
        """
        cli_ctx = CliContextManager.create(modifiers=CliModifiers.from_click_ctx(ctx))
        remote_opts = CliRemoteOpts.from_click_ctx(ctx)
        Evaluator.eval_cli_entrypoint_step(
            name="Raspbian OS Configure",
            call=lambda: RPiOsConfigureCmd().run(ctx=cli_ctx, args=RPiOsConfigureCmdArgs(remote_opts=remote_opts)),
            error_message="Failed to configure Raspbian OS",
            verbose=cli_ctx.is_verbose(),
        )

    @cli_group.command()
    @click.option(
        "--static-ip-address",
        type=str,
        help="Static IP address to set as the remote host IP address",
        show_default=False,
        envvar="PROV_RPI_STATIC_IP",
    )
    @click.option(
        "--gw-ip-address",
        type=str,
        help="Internet gateway address / home router address",
        show_default=False,
        envvar="PROV_GATEWAY_ADDRESS",
    )
    @click.option(
        "--dns-ip-address",
        type=str,
        help="Domain name server address / home router address",
        show_default=False,
        envvar="PROV_DNS_ADDRESS",
    )
    @click.pass_context
    def network(
        ctx: click.Context,
        static_ip_address: Optional[str],
        gw_ip_address: Optional[str],
        dns_ip_address: Optional[str],
    ) -> None:
        """
        Select a remote Raspberry Pi node on the ethernet network to configure a static IP address.
        """
        cli_ctx = CliContextManager.create(modifiers=CliModifiers.from_click_ctx(ctx))
        remote_opts = CliRemoteOpts.from_click_ctx(ctx)
        Evaluator.eval_cli_entrypoint_step(
            name="Raspbian Network Configure",
            call=lambda: RPiNetworkConfigureCmd().run(
                ctx=cli_ctx,
                args=RPiNetworkConfigureCmdArgs(
                    gw_ip_address=gw_ip_address,
                    dns_ip_address=dns_ip_address,
                    static_ip_address=static_ip_address,
                    remote_opts=remote_opts,
                ),
            ),
            error_message="Failed to configure RPi network",
            verbose=cli_ctx.is_verbose(),
        )
