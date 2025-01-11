#!/usr/bin/env python3

import pathlib

import click
from components.runtime.cli.cli_modifiers import cli_modifiers
from components.runtime.cli.menu_format import CustomGroup
from components.runtime.cli.version import append_version_cmd_to_cli

from provisioner_examples_plugin.src.anchor.cli import register_anchor_commands

# from provisioner_shared.components.vcs.typer_vcs_opts import TyperVersionControl
from provisioner_examples_plugin.src.ansible.cli import register_ansible_commands
from provisioner_examples_plugin.src.config.domain.config import PLUGIN_NAME, ExamplesConfig
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager

# from provisioner_examples_plugin.src.anchor.cli import register_anchor_commands

EXAMPLES_PLUGINS_ROOT_PATH = str(pathlib.Path(__file__).parent)
CONFIG_INTERNAL_PATH = f"{EXAMPLES_PLUGINS_ROOT_PATH}/resources/config.yaml"


def load_config():
    # Load plugin configuration
    ConfigManager.instance().load_plugin_config(PLUGIN_NAME, CONFIG_INTERNAL_PATH, cls=ExamplesConfig)


def append_to_cli(root_menu: click.Group):
    examples_cfg = ConfigManager.instance().get_plugin_config(PLUGIN_NAME)
    if examples_cfg.remote is None:
        raise Exception("Remote configuration is mandatory and missing from plugin configuration")

    @root_menu.group(invoke_without_command=True, no_args_is_help=True, cls=CustomGroup)
    @cli_modifiers
    @click.pass_context
    def examples(ctx):
        """Playground for using the CLI framework with basic dummy commands"""
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    append_version_cmd_to_cli(
        root_menu=examples, root_package=EXAMPLES_PLUGINS_ROOT_PATH, description="Print examples plugin version"
    )

    register_ansible_commands(cli_group=examples, remote_config=examples_cfg.remote)

    register_anchor_commands(
        cli_group=examples,
        remote_config=examples_cfg.remote,
        vcs_config=examples_cfg.vcs,
    )
