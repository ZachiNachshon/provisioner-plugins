#!/usr/bin/env python3


from loguru import logger
from provisioner_installers_plugin.src.k3s.cmd.remote_k3s_gather_info import (
    RemoteK3sGatherInfoArgs,
    RemoteK3sGatherInfoRunner,
)

from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators


class K3sGatherInfoCmdArgs:

    remote_opts: RemoteOpts

    def __init__(self, remote_opts: RemoteOpts = None) -> None:
        self.remote_opts = remote_opts

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()
        logger.debug("K3sGatherInfoCmdArgs: \n")


class K3sGatherInfoCmd:
    def run(self, ctx: Context, args: K3sGatherInfoCmdArgs) -> None:
        logger.debug("Inside K3sGatherInfoCmd run()")
        args.print()

        RemoteK3sGatherInfoRunner().run(
            ctx=ctx,
            args=RemoteK3sGatherInfoArgs(
                remote_opts=args.remote_opts,
            ),
            collaborators=CoreCollaborators(ctx),
        )
