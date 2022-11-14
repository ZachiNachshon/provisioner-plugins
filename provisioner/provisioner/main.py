#!/usr/bin/env python3

import typer
from python_core_lib.cli.entrypoint import main_runner

from provisioner.rpi.os.cli import rpi_cli_app
from provisioner.example.dummy.cli import dummy_cli_app

# Use invoke_without_command=True to allow usage of --version flags which are NoOp commands
# Use also no_args_is_help=True to print the help menu is no arguments were supplied
app = typer.Typer(callback=main_runner, invoke_without_command=True, no_args_is_help=True)
app.add_typer(rpi_cli_app, name="rpi", invoke_without_command=True, no_args_is_help=True)
app.add_typer(dummy_cli_app, name="dummy", invoke_without_command=True, no_args_is_help=True)


def main():
    app()
