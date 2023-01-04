#!/usr/bin/env python3

import typer

from provisioner_single_board_plugin.raspberry_pi.node.cli import rpi_node_cli_app
from provisioner_single_board_plugin.raspberry_pi.os.cli import rpi_os_cli_app
from provisioner_features_lib.remote.typer_remote_opts_callback import remote_args_callback

def register_raspberry_pi_commands(app: typer.Typer, callback_remote_args):
    
    single_board_cli_app = typer.Typer()
    app.add_typer(single_board_cli_app, name="raspberry-pi", invoke_without_command=True, no_args_is_help=True)    

    single_board_cli_app.add_typer(
        rpi_node_cli_app, 
        name="node", 
        invoke_without_command=True, 
        no_args_is_help=True, 
        callback=remote_args_callback)

    single_board_cli_app.add_typer(
        rpi_os_cli_app, 
        name="os", 
        invoke_without_command=True, 
        no_args_is_help=True)
