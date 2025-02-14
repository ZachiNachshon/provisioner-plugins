#!/usr/bin/env python3

from loguru import logger

from provisioner_shared.components.anchor.anchor_runner import (
    AnchorCmdRunner,
    AnchorRunnerCmdArgs,
)
from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.vcs.vcs_opts import CliVersionControlOpts


class AnchorCmdArgs:

    anchor_run_command: str
    vcs_opts: CliVersionControlOpts
    remote_opts: RemoteOpts

    def __init__(
        self,
        anchor_run_command: str,
        vcs_opts: CliVersionControlOpts = None,
        remote_opts: RemoteOpts = None,
    ) -> None:

        self.anchor_run_command = anchor_run_command
        self.vcs_opts = vcs_opts
        self.remote_opts = remote_opts

    def print(self) -> None:
        if self.remote_opts:
            print(self.remote_opts)
            self.remote_opts.print()
        logger.debug("AnchorCmdArgs: \n" + f"  anchor_run_command: {self.anchor_run_command}\n")


class AnchorCmd:
    def run(self, ctx: Context, args: AnchorCmdArgs) -> None:
        logger.debug("Inside AnchorCmd run()")
        args.print()

        AnchorCmdRunner().run(
            ctx=ctx,
            args=AnchorRunnerCmdArgs(
                anchor_run_command=args.anchor_run_command,
                vcs_opts=args.vcs_opts,
                remote_opts=args.remote_opts,
            ),
            collaborators=CoreCollaborators(ctx),
        )
