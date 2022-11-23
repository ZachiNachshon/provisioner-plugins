#!/usr/bin/env python3

from typing import Optional

import typer
from loguru import logger
from python_core_lib.cli.state import CliGlobalArgs
from python_core_lib.errors.cli_errors import StepEvaluationFailure
from python_core_lib.infra.context import CliContextManager
from python_features_lib.remote.typer_remote_opts import TyperRemoteOpts

from python_features_lib.config.config_resolver import ConfigResolver
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
    try:
        args = HelloWorldCmdArgs(username=username)
        args.print()
        HelloWorldCmd().run(ctx=CliContextManager.create(), args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to run hello world command. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to run hello world command. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise e
