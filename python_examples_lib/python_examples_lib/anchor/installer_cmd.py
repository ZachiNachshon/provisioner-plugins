#!/usr/bin/env python3

from typing import List

from loguru import logger
from python_core_lib.infra.context import Context
from python_features_lib.remote.domain.config import RunEnvironment

from python_installer_lib.installer.installer_runner import (
    UtilityInstallerCmdRunner,
    UtilityInstallerCmdRunnerCollaborators,
    UtilityInstallerRunnerCmdArgs,
)
from python_features_lib.remote.typer_remote_opts import CliRemoteOpts


class UtilityInstallerCmdArgs:

    utilities: List[str]
    environment: RunEnvironment
    github_access_token: str
    remote_opts: CliRemoteOpts

    def __init__(
        self,
        utilities: List[str],
        environment: RunEnvironment,
        github_access_token: str,
    ) -> None:

        self.utilities = utilities
        self.environment = environment
        self.github_access_token = github_access_token
        self.remote_opts = CliRemoteOpts.maybe_get()

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()
        logger.debug(
            f"InstallerCmdArgs: \n"
            + f"  utilities: {str(self.utilities)}\n"
            + f"  environment: {self.environment}\n"
            + f"  github_access_token: REDACTED\n"
        )


class UtilityInstallerCmd:
    def run(self, ctx: Context, args: UtilityInstallerCmdArgs) -> None:
        logger.debug("Inside UtilityInstallerCmd run()")

        UtilityInstallerCmdRunner().run(
            ctx=ctx,
            args=UtilityInstallerRunnerCmdArgs(
                utilities=args.utilities, github_access_token=args.github_access_token, remote_args=args.remote_opts
            ),
            collaborators=UtilityInstallerCmdRunnerCollaborators(ctx),
            run_env=args.environment,
        )
