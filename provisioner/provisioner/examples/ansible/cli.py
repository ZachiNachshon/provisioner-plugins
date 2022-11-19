#!/usr/bin/env python3

from typing import Optional

import typer
from loguru import logger
from python_core_lib.cli.state import CliGlobalArgs
from python_core_lib.errors.cli_errors import StepEvaluationFailure
from python_core_lib.infra.context import CliContextManager
from python_features_lib.remote.remote_connector import RemoteCliArgs
from python_features_lib.remote.typer_remote_opts import TyperRemoteOpts

from provisioner.config.config_resolver import ConfigResolver
from provisioner.examples.ansible.hello_world_cmd import HelloWorldCmd, HelloWorldCmdArgs

example_ansible_cli_app = typer.Typer()

@example_ansible_cli_app.command(name="hello")
@logger.catch(reraise=True)
def hello(
    username: str = typer.Option(
        "Zachi Nachshon", help="User name to greet with hello world", envvar="DUMMY_HELLO_USERNAME"
    ),
    node_username: Optional[str] = TyperRemoteOpts.node_username(),
    node_password: Optional[str] = TyperRemoteOpts.node_password(),
    ssh_private_key_file_path: Optional[str] = TyperRemoteOpts.ssh_private_key_file_path(),
    ip_discovery_range: Optional[str] = TyperRemoteOpts.ip_discovery_range(),
) -> None:
    """
    Run a dummy hello world scenario locally or on remote machine via Ansible playbook
    """
    try:
        args = HelloWorldCmdArgs(
            username=username,
            node_username=node_username,
            node_password=node_password,
            ssh_private_key_file_path=ssh_private_key_file_path,
            ip_discovery_range=ip_discovery_range,
            host_ip_pairs=RemoteCliArgs.to_host_ip_pairs(ConfigResolver.config.remote.hosts),
        )
        args.print()
        HelloWorldCmd().run(ctx=CliContextManager.create(), args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to run hello world command. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to run hello world command. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise e
