#!/usr/bin/env python3

from typing import Optional
from python_core_lib.infra.evaluator import Evaluator

import typer
from loguru import logger
from provisioner_features_lib.config.config_resolver import ConfigResolver
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.infra.context import CliContextManager

from provisioner_single_board_plugin.raspberry_pi.node.configure_cmd import (
    RPiOsConfigureCmd,
    RPiOsConfigureCmdArgs,
)
from provisioner_single_board_plugin.raspberry_pi.node.network_cmd import (
    RPiNetworkConfigureCmd,
    RPiNetworkConfigureCmdArgs,
)

rpi_node_cli_app = typer.Typer()


@rpi_node_cli_app.command(name="configure")
@logger.catch(reraise=True)
def configure() -> None:
    """
    Select a remote Raspberry Pi node to configure Raspbian OS software and hardware settings.
    Configuration is aimed for an optimal headless Raspberry Pi used as a Kubernetes cluster node.
    """
    Evaluator.eval_cli_entrypoint_step(
        name="Raspbian OS Configure",
        call=lambda: RPiOsConfigureCmd().run(
            ctx=CliContextManager.create(), args=RPiOsConfigureCmdArgs(remote_opts=CliRemoteOpts.maybe_get())
        ),
        error_message="Failed to configure Raspbian OS"
    )
    
@rpi_node_cli_app.command(name="network")
@logger.catch(reraise=True)
def network(
    static_ip_address: Optional[str] = typer.Option(
        None, show_default=False, help="Static IP address to set as the remote host IP address", envvar="RPI_STATIC_IP"
    ),
    gw_ip_address: Optional[str] = typer.Option(
        ConfigResolver.get_config().single_board.network.gw_ip_address,
        help="Internet gateway address / home router address",
        envvar="GATEWAY_ADDRESS",
    ),
    dns_ip_address: Optional[str] = typer.Option(
        ConfigResolver.get_config().single_board.network.dns_ip_address,
        help="Domain name server address / home router address",
        envvar="DNS_ADDRESS",
    ),
) -> None:
    """
    Select a remote Raspberry Pi node on the ethernet network to configure a static IP address.
    """
    Evaluator.eval_cli_entrypoint_step(
        name="Raspbian Network Configure",
        call=lambda: RPiNetworkConfigureCmd().run(
            ctx=CliContextManager.create(),
            args=RPiNetworkConfigureCmdArgs(
                gw_ip_address=gw_ip_address,
                dns_ip_address=dns_ip_address,
                static_ip_address=static_ip_address,
                remote_opts=CliRemoteOpts.maybe_get(),
            ),
        ),
        error_message="Failed to configure RPi network"
    )
