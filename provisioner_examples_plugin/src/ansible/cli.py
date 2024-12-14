#!/usr/bin/env python3


import typer
from loguru import logger

from provisioner_examples_plugin.src.ansible.hello_world_cmd import (
    HelloWorldCmd,
    HelloWorldCmdArgs,
)
from provisioner_shared.components.remote.typer_remote_opts import TyperRemoteOpts
from provisioner_shared.components.runtime.infra.context import CliContextManager
from provisioner_shared.components.runtime.infra.evaluator import Evaluator

example_ansible_cli_app = typer.Typer()

typer_remote_opts: TyperRemoteOpts = None


def register_ansible_commands(app: typer.Typer, remote_opts: TyperRemoteOpts):
    global typer_remote_opts
    typer_remote_opts = remote_opts
    app.add_typer(
        example_ansible_cli_app,
        name="ansible",
        invoke_without_command=True,
        no_args_is_help=True,
    )


@example_ansible_cli_app.command(name="hello")
@logger.catch(reraise=True)
def ansible_hello(
    username: str = typer.Option(
        "Zachi Nachshon",
        help="User name to greet with hello world",
        envvar="DUMMY_HELLO_USERNAME",
    ),
) -> None:
    """
    Run a dummy hello world scenario locally via Ansible playbook
    """
    Evaluator.eval_cli_entrypoint_step(
        name="Ansible Hello World",
        call=lambda: HelloWorldCmd().run(
            ctx=CliContextManager.create(),
            args=HelloWorldCmdArgs(username=username, remote_opts=typer_remote_opts.to_cli_opts()),
        ),
        error_message="Failed to run hello world command",
    )
