#!/usr/bin/env python3

from typing import Callable, Optional

import typer

from python_core_lib.cli.state import CliGlobalArgs
from python_core_lib.infra.log import LoggerManager

STATIC_VERSION_FILE_PATH = None

def main_runner(
    verbose: Optional[bool] = typer.Option(False, "--verbose", "-v", help="Run command with DEBUG verbosity"),
    auto_prompt: Optional[bool] = typer.Option(
        False, "--auto-prompt", "-y", help="Do not prompt for approval and accept everything"
    ),
    dry_run: Optional[bool] = typer.Option(
        False, "--dry-run", "-d", help="Run command as NO-OP, print commands to output, do not execute"
    ),
    os_arch: Optional[str] = typer.Option(None, "--os-arch", help="Specify a OS_ARCH tuple manually"),
    version: Optional[bool] = typer.Option(False, "--version", help="Print client version"),
) -> None:

    if version:
        print(try_read_version())
        typer.Exit(0)

    if verbose:
        typer.echo("Verbose output: enabled")

    if dry_run:
        typer.echo("Dry run: enabled")

    if auto_prompt:
        typer.echo("Auto prompt: enabled")

    if os_arch:
        typer.echo(f"OS_Arch supplied manually: {os_arch}")

    CliGlobalArgs.create(verbose, dry_run, auto_prompt, os_arch)
    logger_mgr = LoggerManager()
    logger_mgr.initialize(verbose, dry_run)

def try_read_version() -> str:
    content = "no version"
    try:
        with open(STATIC_VERSION_FILE_PATH, "r+") as opened_file:
            content = opened_file.read()
            opened_file.close()
    except Exception as error:
        pass
    return content

class EntryPoint:

    @staticmethod
    def create_typer(
        title: str, 
        config_resolver_fn: Optional[Callable] = None, 
        version_file_path: Optional[str] = "resources/version.txt") -> typer.Typer:

        global STATIC_VERSION_FILE_PATH
        STATIC_VERSION_FILE_PATH = version_file_path

        if config_resolver_fn:
            config_resolver_fn()

        # Use invoke_without_command=True to allow usage of --version flags which are NoOp commands
        # Use also no_args_is_help=True to print the help menu if no arguments were supplied
        return typer.Typer(
            help=title,
            callback=main_runner, 
            invoke_without_command=True, 
            no_args_is_help=True, 
            rich_markup_mode=None)
