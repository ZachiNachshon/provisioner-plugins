#!/usr/bin/env python3

import typer

from provisioner.single_board.raspberry_pi.node.cli import rpi_node_cli_app
from provisioner.single_board.raspberry_pi.os.cli import rpi_os_cli_app
from python_features_lib.remote.typer_remote_opts_callback import remote_args_callback

rpi_cli_app = typer.Typer()
rpi_cli_app.add_typer(rpi_node_cli_app, name="node", invoke_without_command=True, no_args_is_help=True, callback=remote_args_callback)
rpi_cli_app.add_typer(rpi_os_cli_app, name="os", invoke_without_command=True, no_args_is_help=True)
