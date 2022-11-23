#!/usr/bin/env python3


import typer
from loguru import logger
from python_core_lib.cli.state import CliGlobalArgs
from python_core_lib.errors.cli_errors import StepEvaluationFailure
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
    try:
        args = AnchorCmdArgs(
            anchor_run_command=anchor_run_command,
            github_organization=github_organization,
            repository_name=repository_name,
            branch_name=branch_name,
            github_access_token=git_access_token,
        )
        args.print()
        AnchorCmd().run(ctx=CliContextManager.create(), args=args)
    except StepEvaluationFailure as sef:
        logger.critical("Failed to run anchor command. ex: {}, message: {}", sef.__class__.__name__, str(sef))
    except Exception as e:
        logger.critical("Failed to run anchor command. ex: {}, message: {}", e.__class__.__name__, str(e))
        if CliGlobalArgs.is_verbose():
            raise e

