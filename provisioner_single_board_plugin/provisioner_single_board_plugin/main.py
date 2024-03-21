#!/usr/bin/env python3

import pathlib

import typer
from provisioner.config.manager.config_manager import ConfigManager
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts

from provisioner_single_board_plugin.config.domain.config import SINGLE_BOARD_PLUGIN_NAME, SingleBoardConfig

CONFIG_INTERNAL_PATH = f"{pathlib.Path(__file__).parent.parent}/resources/config.yaml"

typer_remote_opts: TyperRemoteOpts = None


def load_config():
    # Load plugin configuration
    ConfigManager.instance().load_plugin_config(SINGLE_BOARD_PLUGIN_NAME, CONFIG_INTERNAL_PATH, cls=SingleBoardConfig)


def append_to_cli(app: typer.Typer):
    single_board_cfg = ConfigManager.instance().get_plugin_config(SINGLE_BOARD_PLUGIN_NAME)
    if single_board_cfg.remote is None:
        raise Exception("Remote configuration is mandatory and missing from plugin configuration")

    typer_remote_opts = TyperRemoteOpts(single_board_cfg.remote)

    # Create the CLI structure
    single_board_cli_app = typer.Typer()
    app.add_typer(
        single_board_cli_app,
        name="single-board",
        invoke_without_command=True,
        no_args_is_help=True,
        help="Single boards management as simple as it gets",
        callback=typer_remote_opts.as_typer_callback(),
    )

    from provisioner_single_board_plugin.raspberry_pi.cli import (
        register_raspberry_pi_commands,
    )

    register_raspberry_pi_commands(app=single_board_cli_app, remote_opts=typer_remote_opts)
