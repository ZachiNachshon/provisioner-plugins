#!/usr/bin/env python3


from python_features_lib.remote.typer_remote_opts_callback import remote_args_callback
import typer

from provisioner.examples.ansible.cli import example_ansible_cli_app
from provisioner.examples.anchor.cli import example_anchor_cli_app

examples_cli_app = typer.Typer()
examples_cli_app.add_typer(example_ansible_cli_app, name="ansible", invoke_without_command=True, no_args_is_help=True)
examples_cli_app.add_typer(example_anchor_cli_app, name="anchor", invoke_without_command=True, no_args_is_help=True, callback=remote_args_callback)
