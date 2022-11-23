#!/usr/bin/env python3

from typing import List, Optional

from loguru import logger
from python_core_lib.infra.context import Context
from python_core_lib.runner.ansible.ansible import HostIpPair

from provisioner.common.dummy.hello_world_runner import (
    HelloWorldRunner,
    HelloWorldRunnerArgs,
    HelloWorldRunnerCollaborators,
)
from python_features_lib.remote.typer_remote_opts import CliRemoteOpts


HelloWorldAnsiblePlaybookRelativePathFromRoot = "provisioner/examples/ansible/playbooks/hello_world.yaml"

class HelloWorldCmdArgs:

    username: str
    remote_opts: CliRemoteOpts

    def __init__(self, username: str = None) -> None:
        self.username = username
        self.remote_opts = CliRemoteOpts.maybe_get()

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()
        logger.debug(f"HelloWorldCmdArgs: \n" + f"  username: {self.username}\n")


class HelloWorldCmd:
    def run(self, ctx: Context, args: HelloWorldCmdArgs) -> None:
        logger.debug("Inside HelloWorldCmd run()")

        HelloWorldRunner().run(
            ctx=ctx,
            args=HelloWorldRunnerArgs(
                username=args.username,
                remote_opts=args.remote_opts,
                ansible_playbook_relative_path_from_root=HelloWorldAnsiblePlaybookRelativePathFromRoot,
            ),
            collaborators=HelloWorldRunnerCollaborators(ctx),
        )
