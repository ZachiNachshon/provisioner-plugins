#!/usr/bin/env python3


import typer
from loguru import logger
from python_core_lib.infra.context import CliContextManager
from python_core_lib.infra.evaluator import Evaluator

from provisioner_examples_plugin.ansible.hello_world_cmd import HelloWorldCmd, HelloWorldCmdArgs

example_ansible_cli_app = typer.Typer()

def register_ansible_commands(app: typer.Typer):
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
        "Zachi Nachshon", help="User name to greet with hello world", envvar="DUMMY_HELLO_USERNAME"
    ),
) -> None:
    """
    Run a dummy hello world scenario locally via Ansible playbook
    """
    Evaluator.eval_cli_entrypoint_step(
        ctx=CliContextManager.create(),
        err_msg="Failed to run hello world command",
        call=lambda: HelloWorldCmd().run(ctx=CliContextManager.create(), args=HelloWorldCmdArgs(username=username)),
    )
