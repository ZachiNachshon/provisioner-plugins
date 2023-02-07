#!/usr/bin/env python3


from loguru import logger
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.infra.context import Context
from python_core_lib.shared.collaborators import CoreCollaborators

from provisioner_examples_plugin.ansible.hello_world_runner import (
    HelloWorldRunner,
    HelloWorldRunnerArgs,
)

# When reading Ansible static files from within `provisioner_examples_plugin` module,
# it should be read as relative from the module root folder
HelloWorldAnsiblePlaybookRelativePathFromModule = "provisioner_examples_plugin/ansible/playbooks/hello_world.yaml"


class HelloWorldCmdArgs:

    username: str
    remote_opts: CliRemoteOpts

    def __init__(self, username: str = None, remote_opts: CliRemoteOpts = None) -> None:
        self.username = username
        self.remote_opts = remote_opts

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()
        logger.debug(f"HelloWorldCmdArgs: \n" + f"  username: {self.username}\n")


class HelloWorldCmd:
    def run(self, ctx: Context, args: HelloWorldCmdArgs) -> None:
        logger.debug("Inside HelloWorldCmd run()")
        args.print()

        HelloWorldRunner().run(
            ctx=ctx,
            args=HelloWorldRunnerArgs(
                username=args.username,
                remote_opts=args.remote_opts,
                ansible_playbook_relative_path_from_module=HelloWorldAnsiblePlaybookRelativePathFromModule,
            ),
            collaborators=CoreCollaborators(ctx),
        )
