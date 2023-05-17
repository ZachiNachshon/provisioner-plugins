#!/usr/bin/env python3

import typer
from provisioner_features_lib.remote.typer_remote_opts_callback import (
    remote_args_callback,
)


def append_to_cli(app: typer.Typer):
    examples_cli = typer.Typer()
    app.add_typer(examples_cli, name="examples", invoke_without_command=True, no_args_is_help=True)

    from provisioner_examples_plugin.anchor.cli import register_anchor_commands

    register_anchor_commands(app=examples_cli, callback_remote_args=remote_args_callback)

    from provisioner_examples_plugin.ansible.cli import register_ansible_commands

    register_ansible_commands(app=examples_cli, callback_remote_args=remote_args_callback)
