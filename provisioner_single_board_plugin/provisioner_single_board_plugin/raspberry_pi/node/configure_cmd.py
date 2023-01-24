#!/usr/bin/env python3


from loguru import logger
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.infra.context import Context
from python_core_lib.shared.collaborators import CoreCollaborators

from provisioner_single_board_plugin.common.remote.remote_os_configure import (
    RemoteMachineOsConfigureArgs,
    RemoteMachineOsConfigureRunner,
)

RpiConfigureOsAnsiblePlaybookRelativePathFromRoot = (
    "provisioner_single_board_plugin/raspberry_pi/node/playbooks/configure_os.yaml"
)


class RPiOsConfigureCmdArgs:

    remote_opts: CliRemoteOpts

    def __init__(self, remote_opts: CliRemoteOpts = CliRemoteOpts.maybe_get()) -> None:
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
                ansible_playbook_relative_path_from_root=RpiConfigureOsAnsiblePlaybookRelativePathFromRoot,
            ),
            collaborators=CoreCollaborators(ctx),
        )
