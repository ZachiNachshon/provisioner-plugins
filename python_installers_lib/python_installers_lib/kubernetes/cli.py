#!/usr/bin/env python3


import typer

# from python_installers_lib.cli.k3s.cli import register_command


def register_kubernetes_commands(app: typer.Typer):
    k8s_apps = typer.Typer()
    # register_command(cli_apps)
    app.add_typer(k8s_apps, name="kubernetes", invoke_without_command=True, no_args_is_help=True)
