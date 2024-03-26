#!/usr/bin/env python3

import os
from typing import Any, List, Optional

from loguru import logger
from provisioner.infra.context import Context
from provisioner.shared.collaborators import CoreCollaborators
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts

from provisioner_installers_plugin.installer.domain.command import InstallerSubCommandName
from provisioner_installers_plugin.installer.domain.dynamic_args import DynamicArgs
from provisioner_installers_plugin.installer.runner.installer_runner import (
    InstallerEnv,
    UtilityInstallerCmdRunner,
    UtilityInstallerRunnerCmdArgs,
)
from provisioner_installers_plugin.installer.utilities import SupportedToolings


class UtilityInstallerCmdArgs:

    utilities: List[str]
    remote_opts: CliRemoteOpts
    git_access_token: str
    sub_command_name: InstallerSubCommandName
    dynamic_args: dict[str, Any]

    def __init__(
        self,
        utilities: List[str],
        remote_opts: CliRemoteOpts,
        sub_command_name: InstallerSubCommandName,
        git_access_token: str = None,
        dynamic_args: Optional[dict[str, Any]] = None,
    ) -> None:

        self.utilities = utilities
        self.remote_opts = remote_opts
        self.dynamic_args = dynamic_args
        self.sub_command_name = sub_command_name
        if git_access_token:
            self.git_access_token = git_access_token
        else:
            self.git_access_token = os.getenv("GITHUB_TOKEN", default="")

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()
        logger.debug(
            "InstallerCmdArgs: \n"
            + f"  utilities: {str(self.utilities)}\n"
            + f"  dynamic_args: {str(self.dynamic_args)}\n"
            + f"  sub_command_name: {str(self.sub_command_name.value)}\n"
            + "  git_access_token: REDACTED\n"
        )


class UtilityInstallerCmd:
    def run(self, ctx: Context, args: UtilityInstallerCmdArgs) -> bool:
        logger.debug("Inside UtilityInstallerCmd run()")
        args.print()
        return UtilityInstallerCmdRunner.run(
            env=InstallerEnv(
                ctx=ctx,
                collaborators=CoreCollaborators(ctx),
                supported_utilities=SupportedToolings,
                args=UtilityInstallerRunnerCmdArgs(
                    utilities=args.utilities,
                    remote_opts=args.remote_opts,
                    sub_command_name=args.sub_command_name,
                    git_access_token=args.git_access_token,
                    dynamic_args=DynamicArgs(args.dynamic_args),
                ),
            )
        )
