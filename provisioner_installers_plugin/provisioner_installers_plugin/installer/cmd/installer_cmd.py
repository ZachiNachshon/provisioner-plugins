#!/usr/bin/env python3

from typing import List

from loguru import logger
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.infra.context import Context
from python_core_lib.shared.collaborators import CoreCollaborators

from provisioner_installers_plugin.installer.runner.installer_runner import (
    Env,
    UtilityInstallerCmdRunner,
    UtilityInstallerRunnerCmdArgs,
)
from provisioner_installers_plugin.installer.utilities import SupportedToolings


class UtilityInstallerCmdArgs:

    utilities: List[str]
    remote_opts: CliRemoteOpts
    github_access_token: str

    def __init__(
        self,
        utilities: List[str],
        remote_opts: CliRemoteOpts,
        github_access_token: str = None,
    ) -> None:

        self.utilities = utilities
        self.remote_opts = remote_opts
        self.github_access_token = github_access_token

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()
        logger.debug(
            f"InstallerCmdArgs: \n" + f"  utilities: {str(self.utilities)}\n" + f"  github_access_token: REDACTED\n"
        )


class UtilityInstallerCmd:
    def run(self, ctx: Context, args: UtilityInstallerCmdArgs) -> bool:
        logger.debug("Inside UtilityInstallerCmd run()")
        args.print()
        return UtilityInstallerCmdRunner.run(
            env=Env(
                ctx=ctx,
                collaborators=CoreCollaborators(ctx),
                supported_utilities=SupportedToolings,
                args=UtilityInstallerRunnerCmdArgs(
                    utilities=args.utilities, remote_opts=args.remote_opts, github_access_token=args.github_access_token
                ),
            )
        )
