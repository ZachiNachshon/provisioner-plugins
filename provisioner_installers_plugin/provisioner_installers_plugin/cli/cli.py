#!/usr/bin/env python3

import typer

from provisioner_installers_plugin.cli.anchor.cli import anchor
from provisioner_installers_plugin.cli.helm.cli import helm
from provisioner_installers_plugin.cli.k3s.cli import k3s_agent, k3s_server

# InstallablesJsonFilePath = f"{pathlib.Path(__file__).parent}/installables.json"


def get_all_cli_items():
    pass


def get_all_kubernetes_items():
    pass


cli_apps = typer.Typer()


def register_cli_commands(app: typer.Typer, callback_remote_args):

    cli_apps.command("anchor")(anchor)
    cli_apps.command("helm")(helm)
    cli_apps.command("k3s-server")(k3s_server)
    cli_apps.command("k3s-agent")(k3s_agent)
    # cli_apps.command("test")(k3s_server)
    # cli_apps.command("docker")(k3s_server)

    app.add_typer(
        cli_apps, name="cli", invoke_without_command=True, no_args_is_help=True, callback=callback_remote_args
    )
