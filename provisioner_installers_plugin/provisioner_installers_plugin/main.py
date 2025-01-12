#!/usr/bin/env python3
import pathlib

import click
from components.runtime.cli.cli_modifiers import cli_modifiers
from components.runtime.cli.menu_format import CustomGroup
from components.runtime.cli.version import append_version_cmd_to_cli

from provisioner_installers_plugin.src.cli.cli import register_cli_commands
from provisioner_installers_plugin.src.config.domain.config import PLUGIN_NAME, InstallersConfig
from provisioner_installers_plugin.src.k3s.cli import register_k3s_commands
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager

INSTALLERS_PLUGINS_ROOT_PATH = str(pathlib.Path(__file__).parent)
CONFIG_INTERNAL_PATH = f"{INSTALLERS_PLUGINS_ROOT_PATH}/resources/config.yaml"


def load_config():
    ConfigManager.instance().load_plugin_config(PLUGIN_NAME, CONFIG_INTERNAL_PATH, cls=InstallersConfig)


def append_to_cli(root_menu: click.Group):
    installers_cfg = ConfigManager.instance().get_plugin_config(PLUGIN_NAME)
    if installers_cfg.remote is None:
        raise Exception("Remote configuration is mandatory and missing from plugin configuration")

    @root_menu.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_modifiers
    @click.pass_context
    def install(ctx):
        """Install anything anywhere on any OS/Arch either on a local or remote machine"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    append_version_cmd_to_cli(
        root_menu=install, root_package=INSTALLERS_PLUGINS_ROOT_PATH, description="Print installer plugin version"
    )

    register_cli_commands(cli_group=install, installers_cfg=installers_cfg)

    register_k3s_commands(cli_group=install, installers_cfg=installers_cfg)
