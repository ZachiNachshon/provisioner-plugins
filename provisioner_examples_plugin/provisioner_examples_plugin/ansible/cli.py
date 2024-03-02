#!/usr/bin/env python3


import typer
from loguru import logger
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from provisioner.infra.context import CliContextManager
from provisioner.infra.evaluator import Evaluator

from provisioner_examples_plugin.ansible.hello_world_cmd import (
    HelloWorldCmd,
    HelloWorldCmdArgs,
)

example_ansible_cli_app = typer.Typer()


def register_ansible_commands(app: typer.Typer, callback_remote_args):
    app.add_typer(
        example_ansible_cli_app,
        name="ansible",
        invoke_without_command=True,
        no_args_is_help=True,
        callback=callback_remote_args,
    )


# @example_ansible_cli_app.command(name="hello")
# @logger.catch(reraise=True)
# def ansible_hello(
#     username: str = typer.Option(
#         "Zachi Nachshon", help="User name to greet with hello world", envvar="DUMMY_HELLO_USERNAME"
#     ),
# ) -> None:
    
@example_ansible_cli_app.command(name="hello")
@logger.catch(reraise=True)
def ansible_hello(**kwargs) -> None:
    """
    Run a dummy hello world scenario locally via Ansible playbook
    """
    Evaluator.eval_cli_entrypoint_step(
        name="Ansible Hello World",
        call=lambda: HelloWorldCmd().run(
            ctx=CliContextManager.create(),
            # args=HelloWorldCmdArgs(username=kwargs.username, remote_opts=CliRemoteOpts.maybe_get()),
            args=HelloWorldCmdArgs(username=kwargs.username),
        ),
        error_message="Failed to run hello world command",
    )
