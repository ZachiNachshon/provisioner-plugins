#!/usr/bin/env python3

from typing import Optional

from loguru import logger
from python_core_lib.infra.context import Context
from python_single_board_lib.common.remote.remote_network_configure import (
    RemoteMachineNetworkConfigureArgs,
    RemoteMachineNetworkConfigureRunner,
)
from python_core_lib.shared.collaborators import CoreCollaborators
from python_features_lib.remote.typer_remote_opts import CliRemoteOpts

RpiNetworkConfigureAnsiblePlaybookRelativePathFromRoot = "provisioner/single_board/raspberry_pi/node/playbooks/configure_network.yaml"


class RPiNetworkConfigureCmdArgs:

    gw_ip_address: str
    dns_ip_address: str
    static_ip_address: str
    remote_opts: CliRemoteOpts

    def __init__(
        self,
        gw_ip_address: Optional[str] = None,
        dns_ip_address: Optional[str] = None,
        static_ip_address: Optional[str] = None
    ) -> None:
        self.gw_ip_address = gw_ip_address
        self.dns_ip_address = dns_ip_address
        self.static_ip_address = static_ip_address
        self.remote_opts = CliRemoteOpts.maybe_get()

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()
        logger.debug(
            f"RPiNetworkConfigureCmdArgs: \n"
            + f"  gw_ip_address: {self.gw_ip_address}\n"
            + f"  dns_ip_address: {self.dns_ip_address}\n"
            + f"  static_ip_address: {self.static_ip_address}\n"
        )


class RPiNetworkConfigureCmd:
    def run(self, ctx: Context, args: RPiNetworkConfigureCmdArgs) -> None:
        logger.debug("Inside RPiNetworkConfigureCmd run()")

        RemoteMachineNetworkConfigureRunner().run(
            ctx=ctx,
            args=RemoteMachineNetworkConfigureArgs(
                remote_args=args.remote_opts,
                gw_ip_address=args.gw_ip_address,
                dns_ip_address=args.dns_ip_address,
                static_ip_address=args.static_ip_address,
                ansible_playbook_relative_path_from_root=RpiNetworkConfigureAnsiblePlaybookRelativePathFromRoot,
            ),
            collaborators=CoreCollaborators(ctx),
        )
