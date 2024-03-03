#!/usr/bin/env python3

import pathlib
from provisioner.config.manager.config_manager import ConfigManager
import typer
# from provisioner_features_lib.remote.typer_remote_opts_callback import (
#     remote_args_callback,
# )

from provisioner_examples_plugin.config.domain.config import PLUGIN_NAME, ExamplesConfig

CONFIG_INTERNAL_PATH = f"{pathlib.Path(__file__).parent.parent}/resources/config.yaml"

def append_to_cli(app: typer.Typer):
    # Load the plugin configuration
    ConfigManager.instance().load_plugin_config(PLUGIN_NAME, CONFIG_INTERNAL_PATH, cls=ExamplesConfig)
    examples_cfg = ConfigManager.instance().get_plugin_config(PLUGIN_NAME)
    if examples_cfg.remote == None:
        raise Exception("Remote configuration not found in plugin configuration")
    
    # Create the CLI structure
    examples_cli = typer.Typer()
    app.add_typer(
        examples_cli,
        name="examples",
        invoke_without_command=True,
        no_args_is_help=True,
        help="Playground for using the CLI framework with basic dummy commands",
    )

    # from provisioner_examples_plugin.anchor.cli import register_anchor_commands

    # register_anchor_commands(app=examples_cli, callback_remote_args=remote_args_callback)

    # from provisioner_examples_plugin.ansible.cli import register_ansible_commands

    # register_ansible_commands(app=examples_cli, callback_remote_args=remote_args_callback)
