#!/usr/bin/env python3

import pathlib

import typer
from provisioner.config.manager.config_manager import ConfigManager
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts

from provisioner_installers_plugin.config.domain.config import PLUGIN_NAME, InstallersConfig

CONFIG_INTERNAL_PATH = f"{pathlib.Path(__file__).parent.parent}/resources/config.yaml"


def load_config():
    # Load plugin configuration
    ConfigManager.instance().load_plugin_config(PLUGIN_NAME, CONFIG_INTERNAL_PATH, cls=InstallersConfig)


def append_to_cli(app: typer.Typer):
    installers_cfg = ConfigManager.instance().get_plugin_config(PLUGIN_NAME)
    if installers_cfg.remote is None:
        raise Exception("Remote configuration is mandatory and missing from plugin configuration")

    typer_remote_opts = TyperRemoteOpts(installers_cfg.remote)

    installers_cli = typer.Typer()
    app.add_typer(
        installers_cli,
        name="install",
        invoke_without_command=True,
        no_args_is_help=True,
        help="Install anything anywhere on any OS/Arch either on a local or remote machine",
        callback=typer_remote_opts.as_typer_callback(),
    )

    from provisioner_installers_plugin.cli.cli import register_cli_commands

    register_cli_commands(app=installers_cli, remote_opts=typer_remote_opts)

    from provisioner_installers_plugin.k3s.cli import register_k3s_commands

    register_k3s_commands(app=installers_cli, remote_opts=typer_remote_opts)
