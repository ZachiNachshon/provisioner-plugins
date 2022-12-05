#!/usr/bin/env python3


from python_core_lib.infra.evaluator import Evaluator
import typer
from loguru import logger
from python_core_lib.infra.context import CliContextManager

from python_features_lib.config.config_resolver import ConfigResolver
from provisioner.examples.anchor.anchor_cmd import AnchorCmd, AnchorCmdArgs

example_anchor_cli_app = typer.Typer()


@example_anchor_cli_app.command(name="run-command")
@logger.catch(reraise=True)
def run_command(
    anchor_run_command: str = typer.Option(
        ...,
        show_default=False,
        help="Anchor run command (<cmd-name> run <category> --action=do-something)",
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
        ))
    )
    