#!/usr/bin/env python3

import typer

from python_features_lib.remote.typer_remote_opts_callback import remote_args_callback

def append_single_boards(app: typer.Typer):
    single_board_cli_app = typer.Typer()
    app.add_typer(single_board_cli_app, name="single-board", invoke_without_command=True, no_args_is_help=True)

    from python_single_board_lib.raspberry_pi.cli import register_raspberry_pi_commands
    register_raspberry_pi_commands(app=single_board_cli_app, callback_remote_args=remote_args_callback)
