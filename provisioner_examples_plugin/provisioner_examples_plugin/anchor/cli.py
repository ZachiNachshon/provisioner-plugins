#!/usr/bin/env python3


import typer
from loguru import logger
from provisioner.infra.context import CliContextManager
from provisioner.infra.evaluator import Evaluator
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts
from provisioner_features_lib.vcs.typer_vcs_opts import TyperVersionControlOpts

from provisioner_examples_plugin.anchor.anchor_cmd import AnchorCmd, AnchorCmdArgs

example_anchor_cli_app = typer.Typer()

typer_remote_opts: TyperRemoteOpts = None
typer_vcs_opts: TyperVersionControlOpts = None


def register_anchor_commands(app: typer.Typer, remote_opts: TyperRemoteOpts, vcs_opts: TyperVersionControlOpts):
    global typer_remote_opts
    typer_remote_opts = remote_opts
    global typer_vcs_opts
    typer_vcs_opts = vcs_opts
    app.add_typer(
        example_anchor_cli_app,
        name="anchor",
        invoke_without_command=True,
        no_args_is_help=True,
        callback=typer_vcs_opts.as_typer_callback(),
    )


@example_anchor_cli_app.command(name="run-command")
@logger.catch(reraise=True)
def run_anchor_command(
    anchor_run_command: str = typer.Option(
        ...,
        show_default=False,
        help="Anchor run command (without 'anchor' command)",
        envvar="ANCHOR_RUN_COMMAND",
    ),
) -> None:
    """
    Run a dummy anchor run scenario locally or on remote machine via Ansible playbook
    """
    Evaluator.eval_cli_entrypoint_step(
        name="Run Anchor Command",
        call=lambda: AnchorCmd().run(
            ctx=CliContextManager.create(),
            args=AnchorCmdArgs(
                anchor_run_command=anchor_run_command,
                vcs_opts=typer_vcs_opts.to_cli_opts(),
                remote_opts=typer_remote_opts.to_cli_opts(),
            ),
        ),
        error_message="Failed to run anchor command",
    )
