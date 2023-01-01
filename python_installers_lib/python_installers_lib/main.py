#!/usr/bin/env python3

import typer

from python_features_lib.remote.typer_remote_opts_callback import remote_args_callback

def append_installers(app: typer.Typer):
    installers_cli = typer.Typer()
    app.add_typer(installers_cli, name="install", invoke_without_command=True, no_args_is_help=True)

    from python_installers_lib.cli.cli import register_cli_commands
    register_cli_commands(app=installers_cli, callback_remote_args=remote_args_callback)

    from python_installers_lib.kubernetes.cli import register_kubernetes_commands
    register_kubernetes_commands(app=installers_cli)
    
