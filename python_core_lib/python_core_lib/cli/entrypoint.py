#!/usr/bin/env python3

from typing import Callable, Optional

import typer

from ..cli.state import CliGlobalArgs
from ..infra.log import LoggerManager

STATIC_VERISON_FILE_PATH = None

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
        with open(STATIC_VERISON_FILE_PATH, "r+") as opened_file:
            content = opened_file.read()
            opened_file.close()
    except Exception as error:
        pass
    return content

class EntryPoint:

    @staticmethod
    def create_typer(
        title: str, 
        config_resolver_fn: Callable, 
        version_file_path: Optional[str] = "resources/version.txt") -> typer.Typer:

        global STATIC_VERISON_FILE_PATH
        STATIC_VERISON_FILE_PATH = version_file_path

        config_resolver_fn()
        return typer.Typer(
            help=title,
            callback=main_runner, 
            invoke_without_command=True, 
            no_args_is_help=True, 
            rich_markup_mode=None)