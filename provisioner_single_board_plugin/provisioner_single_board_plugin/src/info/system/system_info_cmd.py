#!/usr/bin/env python3


from loguru import logger
from provisioner_single_board_plugin.src.common.remote.remote_system_info_collector import (
    RemoteMachineSystemInfoCollectArgs,
    RemoteMachineSystemInfoCollectRunner,
)

from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators


class SystemInfoCmdArgs:
    """Arguments for the SystemInfoCmd"""

    remote_opts: RemoteOpts

    def __init__(self, remote_opts: RemoteOpts = None) -> None:
        self.remote_opts = remote_opts

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()
        logger.debug("SystemInfoCmdArgs: \n")


class SystemInfoCmd:
    def run(self, ctx: Context, args: SystemInfoCmdArgs) -> None:
        logger.debug("Inside SystemInfoCmd run()")
        args.print()

        RemoteMachineSystemInfoCollectRunner().run(
            ctx=ctx,
            args=RemoteMachineSystemInfoCollectArgs(
                remote_opts=args.remote_opts,
            ),
            collaborators=CoreCollaborators(ctx),
        )
