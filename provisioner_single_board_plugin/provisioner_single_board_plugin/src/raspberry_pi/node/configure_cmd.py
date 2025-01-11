#!/usr/bin/env python3


from loguru import logger
from provisioner_single_board_plugin.src.common.remote.remote_os_configure import (
    RemoteMachineOsConfigureArgs,
    RemoteMachineOsConfigureRunner,
)

from provisioner_shared.components.remote.remote_opts import CliRemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators


class RPiOsConfigureCmdArgs:

    remote_opts: CliRemoteOpts

    def __init__(self, remote_opts: CliRemoteOpts = None) -> None:
        self.remote_opts = remote_opts

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()
        logger.debug("RPiOsConfigureCmdArgs: \n")


class RPiOsConfigureCmd:
    def run(self, ctx: Context, args: RPiOsConfigureCmdArgs) -> None:
        logger.debug("Inside RPiOsConfigureCmd run()")
        args.print()

        RemoteMachineOsConfigureRunner().run(
            ctx=ctx,
            args=RemoteMachineOsConfigureArgs(
                remote_opts=args.remote_opts,
            ),
            collaborators=CoreCollaborators(ctx),
        )
