#!/usr/bin/env python3

import pathlib

import click
from components.runtime.cli.cli_modifiers import cli_modifiers
from components.runtime.cli.menu_format import CustomGroup
from components.runtime.cli.version import append_version_cmd_to_cli
from provisioner_single_board_plugin.src.config.domain.config import SINGLE_BOARD_PLUGIN_NAME, SingleBoardConfig
from provisioner_single_board_plugin.src.raspberry_pi.cli import (
    register_raspberry_pi_commands,
)

from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager

SINGLE_BOARD_PLUGINS_ROOT_PATH = str(pathlib.Path(__file__).parent)
CONFIG_INTERNAL_PATH = f"{SINGLE_BOARD_PLUGINS_ROOT_PATH}/resources/config.yaml"


def load_config():
    ConfigManager.instance().load_plugin_config(SINGLE_BOARD_PLUGIN_NAME, CONFIG_INTERNAL_PATH, cls=SingleBoardConfig)


def append_to_cli(root_menu: click.Group):
    single_board_cfg = ConfigManager.instance().get_plugin_config(SINGLE_BOARD_PLUGIN_NAME)
    # if single_board_cfg.remote is None:
    # raise Exception("Remote configuration is mandatory and missing from plugin configuration")

    @root_menu.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_modifiers
    @click.pass_context
    def single_board(ctx):
        """Single boards management as simple as it gets"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    append_version_cmd_to_cli(
        root_menu=single_board,
        root_package=SINGLE_BOARD_PLUGINS_ROOT_PATH,
        description="Print single board plugin version",
    )

    register_raspberry_pi_commands(cli_group=single_board, single_board_cfg=single_board_cfg)
