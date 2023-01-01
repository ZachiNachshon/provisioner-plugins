#!/usr/bin/env python3


import typer

from provisioner.single_board.raspberry_pi.cli import rpi_cli_app

single_board_cli_app = typer.Typer()
single_board_cli_app.add_typer(rpi_cli_app, name="raspberry-pi", invoke_without_command=True, no_args_is_help=True)
