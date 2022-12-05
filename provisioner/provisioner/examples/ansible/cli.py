#!/usr/bin/env python3


import typer
from loguru import logger
from python_core_lib.infra.evaluator import Evaluator
from python_core_lib.infra.context import CliContextManager

from provisioner.examples.ansible.hello_world_cmd import HelloWorldCmd, HelloWorldCmdArgs

example_ansible_cli_app = typer.Typer()

@example_ansible_cli_app.command(name="hello")
@logger.catch(reraise=True)
def hello(
    username: str = typer.Option(
        "Zachi Nachshon", help="User name to greet with hello world", envvar="DUMMY_HELLO_USERNAME"
    ),
) -> None:
    """
    Run a dummy hello world scenario locally or on remote machine via Ansible playbook
    """
    Evaluator.eval_cli_entrypoint_step(
        ctx=CliContextManager.create(),
        err_msg="Failed to run hello world command",
        call=lambda: HelloWorldCmd().run(
            ctx=CliContextManager.create(), 
            args=HelloWorldCmdArgs(username=username)
        )
    )
