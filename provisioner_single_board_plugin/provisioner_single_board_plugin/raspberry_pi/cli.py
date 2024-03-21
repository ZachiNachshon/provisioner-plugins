#!/usr/bin/env python3


import typer
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts

from provisioner_single_board_plugin.raspberry_pi.node.cli import register_node_commands, rpi_node_cli_app
from provisioner_single_board_plugin.raspberry_pi.os.cli import rpi_os_cli_app

typer_remote_opts: TyperRemoteOpts = None


def register_raspberry_pi_commands(app: typer.Typer, remote_opts: TyperRemoteOpts):
    global typer_remote_opts
    typer_remote_opts = remote_opts

    single_board_cli_app = typer.Typer()
    app.add_typer(
        single_board_cli_app,
        name="raspberry-pi",
        invoke_without_command=True,
        no_args_is_help=True,
        callback=typer_remote_opts.as_typer_callback(),
    )

    single_board_cli_app.add_typer(rpi_node_cli_app, name="node", invoke_without_command=True, no_args_is_help=True)
    register_node_commands(typer_remote_opts)

    single_board_cli_app.add_typer(rpi_os_cli_app, name="os", invoke_without_command=True, no_args_is_help=True)
