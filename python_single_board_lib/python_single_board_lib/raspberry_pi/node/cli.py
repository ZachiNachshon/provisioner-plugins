#!/usr/bin/env python3

from typing import Optional

import typer
from loguru import logger
from python_core_lib.cli.state import CliGlobalArgs
from python_core_lib.errors.cli_errors import (
    CliApplicationException,
    StepEvaluationFailure,
)
from python_core_lib.infra.context import CliContextManager
from python_features_lib.config.config_resolver import ConfigResolver

from python_single_board_lib.raspberry_pi.node.configure_cmd import RPiOsConfigureCmd, RPiOsConfigureCmdArgs
from python_single_board_lib.raspberry_pi.node.network_cmd import (
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
    try:
        args = RPiOsConfigureCmdArgs()
        args.print()
        RPiOsConfigureCmd().run(ctx=CliContextManager.create(), args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to configure Raspbian OS. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to configure Raspbian OS. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise CliApplicationException(e)


@rpi_node_cli_app.command(name="network")
@logger.catch(reraise=True)
def network(
    static_ip_address: Optional[str] = typer.Option(
        None, show_default=False, help="Static IP address to set as the remote host IP address", envvar="RPI_STATIC_IP"
    ),
    gw_ip_address: Optional[str] = typer.Option(
        ConfigResolver.get_config().rpi.network.gw_ip_address,
        help="Internet gateway address / home router address",
        envvar="GATEWAY_ADDRESS",
    ),
    dns_ip_address: Optional[str] = typer.Option(
        ConfigResolver.get_config().rpi.network.dns_ip_address,
        help="Domain name server address / home router address",
        envvar="DNS_ADDRESS",
    ),
) -> None:
    """
    Select a remote Raspberry Pi node on the ethernet network to configure a static IP address.
    """
    try:
        args = RPiNetworkConfigureCmdArgs(
            gw_ip_address=gw_ip_address,
            dns_ip_address=dns_ip_address,
            static_ip_address=static_ip_address
        )
        args.print()
        RPiNetworkConfigureCmd().run(ctx=CliContextManager.create(), args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to configure RPi network. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to configure RPi network. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise CliApplicationException(e)
