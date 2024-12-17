#!/usr/bin/env python3

import pathlib

import typer

from provisioner_examples_plugin.src.config.domain.config import PLUGIN_NAME, ExamplesConfig
from provisioner_shared.components.remote.typer_remote_opts import TyperRemoteOpts
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager
from provisioner_shared.components.vcs.typer_vcs_opts import TyperVersionControl

CONFIG_INTERNAL_PATH = f"{pathlib.Path(__file__).parent}/resources/config.yaml"

typer_remote_opts: TyperRemoteOpts = None


def load_config():
    # Load plugin configuration
    ConfigManager.instance().load_plugin_config(PLUGIN_NAME, CONFIG_INTERNAL_PATH, cls=ExamplesConfig)


def append_to_cli(app: typer.Typer):
    examples_cfg = ConfigManager.instance().get_plugin_config(PLUGIN_NAME)
    if examples_cfg.remote is None:
        raise Exception("Remote configuration is mandatory and missing from plugin configuration")

    typer_remote_opts = TyperRemoteOpts(examples_cfg.remote)

    # Create the CLI structure
    examples_cli_app = typer.Typer()
    app.add_typer(
        examples_cli_app,
        name="examples",
        invoke_without_command=True,
        no_args_is_help=True,
        help="Playground for using the CLI framework with basic dummy commands",
        callback=typer_remote_opts.as_typer_callback(),
    )

    from provisioner_examples_plugin.src.ansible.cli import register_ansible_commands

    register_ansible_commands(app=examples_cli_app, remote_opts=typer_remote_opts)

    from provisioner_examples_plugin.src.anchor.cli import register_anchor_commands

    register_anchor_commands(
        app=examples_cli_app,
        remote_opts=typer_remote_opts,
        vcs_opts=TyperVersionControl(examples_cfg.vcs),
    )
