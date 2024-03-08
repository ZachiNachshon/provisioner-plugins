#!/usr/bin/env python3

import pathlib

import typer
from provisioner.config.manager.config_manager import ConfigManager
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts
from provisioner_features_lib.vcs.typer_vcs_opts import TyperVersionControlOpts

from provisioner_examples_plugin.config.domain.config import PLUGIN_NAME, ExamplesConfig

CONFIG_INTERNAL_PATH = f"{pathlib.Path(__file__).parent.parent}/resources/config.yaml"

typer_remote_opts: TyperRemoteOpts = None


def append_to_cli(app: typer.Typer):
    # Load plugin configuration
    ConfigManager.instance().load_plugin_config(PLUGIN_NAME, CONFIG_INTERNAL_PATH, cls=ExamplesConfig)
    examples_cfg = ConfigManager.instance().get_plugin_config(PLUGIN_NAME)
    if examples_cfg.remote is None:
        raise Exception("Remote configuration is mandatory and not found in plugin configuration")

    typer_remote_opts = TyperRemoteOpts(examples_cfg.remote)

    # Create the CLI structure
    examples_cli = typer.Typer()
    app.add_typer(
        examples_cli,
        name="examples",
        invoke_without_command=True,
        no_args_is_help=True,
        help="Playground for using the CLI framework with basic dummy commands",
        callback=typer_remote_opts.as_typer_callback(),
    )

    from provisioner_examples_plugin.ansible.cli import register_ansible_commands

    register_ansible_commands(app=examples_cli, remote_opts=typer_remote_opts)

    from provisioner_examples_plugin.anchor.cli import register_anchor_commands

    register_anchor_commands(
        app=examples_cli, remote_opts=typer_remote_opts, vcs_opts=TyperVersionControlOpts(examples_cfg.vcs)
    )
