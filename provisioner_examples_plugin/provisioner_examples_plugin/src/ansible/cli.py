#!/usr/bin/env python3

from typing import Optional

import click

from provisioner_examples_plugin.src.ansible.hello_world_cmd import HelloWorldCmd, HelloWorldCmdArgs
from provisioner_examples_plugin.src.config.domain.config import ExamplesConfig
from provisioner_shared.components.remote.cli_remote_opts import cli_remote_opts
from provisioner_shared.components.remote.domain.config import RemoteConfig
from provisioner_shared.components.remote.remote_opts import CliRemoteOpts
from provisioner_shared.components.runtime.cli.cli_modifiers import cli_modifiers
from provisioner_shared.components.runtime.cli.menu_format import CustomGroup, get_nested_value
from provisioner_shared.components.runtime.cli.modifiers import CliModifiers
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator


def register_ansible_commands(
    cli_group: click.Group,
    examples_cfg: Optional[ExamplesConfig] = None,
):
    from_cfg_username = get_nested_value(examples_cfg, path="hello_world.username", default="Zachi Nachshon")

    @cli_group.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_remote_opts(remote_config=examples_cfg.remote if examples_cfg is not None else RemoteConfig())
    @cli_modifiers
    @click.pass_context
    def ansible(ctx: click.Context):
        """Playground for using the CLI framework with basic dummy commands"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @ansible.command()
    @click.option(
        "--username",
        default=from_cfg_username,
        show_default=True,
        help="User name to greet with hello world",
        envvar="DUMMY_HELLO_USERNAME",
    )
    @cli_modifiers
    @click.pass_context
    def hello(ctx, username: str):
        """
        Run a dummy hello world scenario locally via Ansible playbook
        """
        cli_ctx = CliContextManager.create(modifiers=CliModifiers.from_click_ctx(ctx))
        Evaluator.eval_cli_entrypoint_step(
            name="Ansible Hello World",
            call=lambda: HelloWorldCmd().run(
                ctx=cli_ctx,
                args=HelloWorldCmdArgs(username=username, remote_opts=CliRemoteOpts.from_click_ctx(ctx)),
            ),
            error_message="Failed to run hello world command",
            verbose=cli_ctx.is_verbose(),
        )
