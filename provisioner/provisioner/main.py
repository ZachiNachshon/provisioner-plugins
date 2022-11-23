#!/usr/bin/env python3

import os
import pathlib
from python_core_lib.cli.entrypoint import EntryPoint
from python_features_lib.config.config_resolver import ConfigResolver

from provisioner.config.domain.config import ProvisionerConfig

CONFIG_USER_PATH = os.path.expanduser("~/.config/provisioner/config.yaml")
CONFIG_INTERNAL_PATH = f"{pathlib.Path(__file__).parent}/config/config.yaml"

ConfigResolver.load(CONFIG_INTERNAL_PATH, CONFIG_USER_PATH, class_name=ProvisionerConfig)

app = EntryPoint.create_typer(title="Provision Everything Anywhere")    

from provisioner.single_board.cli import single_board_cli_app
app.add_typer(single_board_cli_app, name="single-board", invoke_without_command=True, no_args_is_help=True)

from provisioner.examples.cli import examples_cli_app
app.add_typer(examples_cli_app, name="examples", invoke_without_command=True, no_args_is_help=True)

try:
    from python_installers_lib.main import append_installers
    append_installers(app)
except Exception as ex:
    print(f"Failed to load python installers. ex: {ex}")

def main():
    app()
