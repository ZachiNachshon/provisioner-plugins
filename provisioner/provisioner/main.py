#!/usr/bin/env python3

from python_core_lib.cli.entrypoint import EntryPoint
from provisioner.config.config_resolver import ConfigResolver

# Use invoke_without_command=True to allow usage of --version flags which are NoOp commands
# Use also no_args_is_help=True to print the help menu is no arguments were supplied
# rich_markup_mode=None, rich_help_panel=""
app = EntryPoint.create_typer(title="Provision Everything Anywhere", config_resolver_fn=lambda: ConfigResolver.get_config())

from provisioner.single_board.cli import single_board_cli_app
app.add_typer(single_board_cli_app, name="single-board", invoke_without_command=True, no_args_is_help=True)

from provisioner.examples.cli import examples_cli_app
app.add_typer(examples_cli_app, name="examples", invoke_without_command=True, no_args_is_help=True)

def main():
    app()
