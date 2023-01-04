#!/usr/bin/env python3


import typer
from loguru import logger
from python_core_lib.infra.context import CliContextManager
from python_core_lib.infra.evaluator import Evaluator
from provisioner_features_lib.config.config_resolver import ConfigResolver

from provisioner_examples_plugin.anchor.anchor_cmd import AnchorCmd, AnchorCmdArgs


def register_anchor_commands(app: typer.Typer, callback_remote_args):
    app.add_typer(
        example_anchor_cli_app,
        name="anchor",
        invoke_without_command=True,
        no_args_is_help=True,
        callback=callback_remote_args,
    )


example_anchor_cli_app = typer.Typer()


@example_anchor_cli_app.command(name="run-command")
@logger.catch(reraise=True)
def run_anchor_command(
    anchor_run_command: str = typer.Option(
        ...,
        show_default=False,
        help="Anchor run command (without 'anchor' command)",
        envvar="ANCHOR_RUN_COMMAND",
    ),
    github_organization: str = typer.Option(
        None, show_default=False, help="GitHub repository organization", envvar="GITHUB_REPO_ORGANIZATION"
    ),
    repository_name: str = typer.Option(None, show_default=False, help="Repository name", envvar="ANCHOR_REPO_NAME"),
    branch_name: str = typer.Option("master", help="Repository branch name", envvar="ANCHOR_REPO_BRANCH_NAME"),
    git_access_token: str = typer.Option(
        ConfigResolver.get_config().anchor.github.github_access_token,
        help="GitHub access token (only for private repos)",
        envvar="GITHUB_ACCESS_TOKEN",
    ),
) -> None:
    """
    Run a dummy anchor run scenario locally or on remote machine via Ansible playbook
    """
    Evaluator.eval_cli_entrypoint_step(
        ctx=CliContextManager.create(),
        err_msg="Failed to run anchor command",
        call=lambda: AnchorCmd().run(
            ctx=CliContextManager.create(),
            args=AnchorCmdArgs(
                anchor_run_command=anchor_run_command,
                github_organization=github_organization,
                repository_name=repository_name,
                branch_name=branch_name,
                github_access_token=git_access_token,
            ),
        ),
    )
