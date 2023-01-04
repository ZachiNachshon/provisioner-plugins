#!/usr/bin/env python3

import typer
from python_core_lib.infra.context import CliContextManager
from python_core_lib.infra.evaluator import Evaluator

from provisioner_installers_plugin.installer.cmd.installer_cmd import (
    UtilityInstallerCmd,
    UtilityInstallerCmdArgs,
)


def k3s_server(
    get_node_token: str = typer.Argument(None, show_default=False, help="Read k3s server node token (NODE_TOKEN)"),
) -> None:
    """
    Lightweight Kubernetes Server
    """
    Evaluator.eval_installer_cli_entrypoint_step(
        ctx=CliContextManager.create(),
        name="k3s-server",
        call=lambda: UtilityInstallerCmd().run(
            ctx=CliContextManager.create(), args=UtilityInstallerCmdArgs(utilities=["k3s-server"])
        ),
    )


def k3s_agent(
    server_token: str = typer.Option(
        ..., show_default=False, help="K3s server node token (NODE_TOKEN)", envvar="K3S_SERVER_NODE_TOKEN"
    ),
    server_address: str = typer.Option(
        ..., show_default=False, help="K3s server address (<ip>:<port>)", envvar="K3S_SERVER_ADDRESS"
    ),
) -> None:
    """
    Lightweight Kubernetes Agent
    """
    Evaluator.eval_installer_cli_entrypoint_step(
        ctx=CliContextManager.create(),
        name="k3s-agent",
        call=lambda: UtilityInstallerCmd().run(
            ctx=CliContextManager.create(), args=UtilityInstallerCmdArgs(utilities=["k3s-agent"])
        ),
    )
