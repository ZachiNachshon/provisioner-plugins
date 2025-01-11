#!/usr/bin/env python3


from typing import Optional

import click
from components.remote.cli_remote_opts import cli_remote_opts
from components.remote.domain.config import RemoteConfig
from components.remote.remote_opts import CliRemoteOpts
from components.runtime.cli.cli_modifiers import cli_modifiers
from components.runtime.cli.menu_format import CustomGroup

from provisioner_examples_plugin.src.ansible.hello_world_cmd import HelloWorldCmd, HelloWorldCmdArgs
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator


def register_ansible_commands(cli_group: click.Group, remote_config: Optional[RemoteConfig] = None):

    @cli_group.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_remote_opts(remote_config=remote_config)
    @cli_modifiers
    @click.pass_context
    def ansible(ctx):
        """Playground for using the CLI framework with basic dummy commands"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @ansible.command()
    @click.option(
        "--username",
        default="Zachi Nachshon",
        help="User name to greet with hello world",
        envvar="DUMMY_HELLO_USERNAME",
    )
    @cli_modifiers
    def hello(username: str):
        """
        Run a dummy hello world scenario locally via Ansible playbook
        """
        Evaluator.eval_cli_entrypoint_step(
            name="Ansible Hello World",
            call=lambda: HelloWorldCmd().run(
                ctx=CliContextManager.create(),
                args=HelloWorldCmdArgs(username=username, remote_opts=CliRemoteOpts.options),
            ),
            error_message="Failed to run hello world command",
        )
