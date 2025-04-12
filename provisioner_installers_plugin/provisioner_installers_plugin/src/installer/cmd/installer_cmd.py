#!/usr/bin/env python3

import os
from typing import Any, List, Optional

from loguru import logger
from provisioner_installers_plugin.src.installer.domain.command import InstallerSubCommandName
from provisioner_installers_plugin.src.installer.runner.installer_runner import (
    InstallerEnv,
    UtilityInstallerCmdRunner,
    UtilityInstallerRunnerCmdArgs,
)
from provisioner_installers_plugin.src.utilities.utilities_cli import SupportedToolingsCli
from provisioner_installers_plugin.src.utilities.utilities_k8s import SupportedToolingsK8s
from provisioner_installers_plugin.src.utilities.utilities_system import SupportedToolingsSystem

from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_installers_plugin.src.installer.domain.version import NameVersionArgsTuple
from provisioner_shared.components.runtime.errors.cli_errors import MissingUtilityException
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators


class UtilityInstallerCmdArgs:

    def __init__(
        self,
        utils_to_install: List[NameVersionArgsTuple],
        remote_opts: RemoteOpts,
        sub_command_name: InstallerSubCommandName,
        git_access_token: str = None,
        force: bool = False,
    ) -> None:

        self.utils_to_install = utils_to_install
        self.remote_opts = remote_opts
        self.sub_command_name = sub_command_name
        self.force = force
        if git_access_token:
            self.git_access_token = git_access_token
        else:
            self.git_access_token = os.getenv("GITHUB_TOKEN", default="")

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()
        logger.debug(
            "InstallerCmdArgs: \n"
            + f"  utilities: {str(self.utils_to_install)}\n"
            + f"  sub_command_name: {str(self.sub_command_name.value)}\n"
            + f"  force: {str(self.force)}\n"
            + "  git_access_token: REDACTED\n"
        )


class UtilityInstallerCmd:
    def run(self, ctx: Context, args: UtilityInstallerCmdArgs) -> bool:
        logger.debug("Inside UtilityInstallerCmd run()")
        args.print()
        supported_utils = get_supported_tooling_for_sub_command(args.sub_command_name)
        return UtilityInstallerCmdRunner.run(
            env=InstallerEnv(
                ctx=ctx,
                collaborators=CoreCollaborators(ctx),
                supported_utilities=supported_utils,
                args=UtilityInstallerRunnerCmdArgs(
                    utilities=args.utils_to_install,
                    remote_opts=args.remote_opts,
                    sub_command_name=args.sub_command_name,
                    git_access_token=args.git_access_token,
                    force=args.force,
                ),
            )
        )


def get_supported_tooling_for_sub_command(sub_cmd_namd: InstallerSubCommandName):
    match (sub_cmd_namd):
        case InstallerSubCommandName.CLI:
            return SupportedToolingsCli
        case InstallerSubCommandName.System:
            return SupportedToolingsSystem
        case InstallerSubCommandName.K8S:
            return SupportedToolingsK8s
        case _:
            raise MissingUtilityException(f"Failed to identify a proper toolings category. command: {sub_cmd_namd}")
