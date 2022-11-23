#!/usr/bin/env python3

from typing import List

from loguru import logger
from python_core_lib.infra.context import Context

from python_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_installers_lib.installer.runner.installer_runner import (
    UtilityInstallerCmdRunner,
    UtilityInstallerCmdRunnerCollaborators,
    UtilityInstallerRunnerCmdArgs,
)

class UtilityInstallerCmdArgs:

    utilities: List[str]
    remote_opts: CliRemoteOpts

    def __init__(
        self,
        utilities: List[str],
    ) -> None:

        self.utilities = utilities
        self.remote_opts = CliRemoteOpts.maybe_get()

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()
        logger.debug(
            f"InstallerCmdArgs: \n"
            + f"  utilities: {str(self.utilities)}\n"
        )


class UtilityInstallerCmd:
    def run(self, ctx: Context, args: UtilityInstallerCmdArgs) -> None:
        logger.debug("Inside UtilityInstallerCmd run()")
        args.print()

        UtilityInstallerCmdRunner().run(
            ctx=ctx,
            args=UtilityInstallerRunnerCmdArgs(
                utilities=args.utilities, 
                remote_opts=args.remote_opts
            ),
            collaborators=UtilityInstallerCmdRunnerCollaborators(ctx),
        )
