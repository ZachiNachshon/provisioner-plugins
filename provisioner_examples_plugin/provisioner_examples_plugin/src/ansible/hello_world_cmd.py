#!/usr/bin/env python3


from loguru import logger

from provisioner_examples_plugin.src.ansible.hello_world_runner import (
    HelloWorldRunner,
    HelloWorldRunnerArgs,
)
from provisioner_shared.components.remote.remote_opts import CliRemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators


class HelloWorldCmdArgs:

    username: str
    remote_opts: CliRemoteOpts

    def __init__(self, username: str = None, remote_opts: CliRemoteOpts = None) -> None:
        self.username = username
        self.remote_opts = remote_opts

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()
        logger.debug("HelloWorldCmdArgs: \n" + f"  username: {self.username}\n")


class HelloWorldCmd:
    def run(self, ctx: Context, args: HelloWorldCmdArgs) -> None:
        logger.debug("Inside HelloWorldCmd run()")
        args.print()

        HelloWorldRunner().run(
            ctx=ctx,
            args=HelloWorldRunnerArgs(
                username=args.username,
                remote_opts=args.remote_opts,
            ),
            collaborators=CoreCollaborators(ctx),
        )
