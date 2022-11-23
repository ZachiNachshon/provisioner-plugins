#!/usr/bin/env python3

from typing import Optional

from loguru import logger
from python_core_lib.infra.context import Context

from python_features_lib.anchor.anchor_runner import (
    AnchorCmdRunner,
    AnchorCmdRunnerCollaborators,
    AnchorRunnerCmdArgs,
)
from python_features_lib.remote.typer_remote_opts import CliRemoteOpts

class AnchorCmdArgs:

    anchor_run_command: str
    github_organization: str
    repository_name: str
    branch_name: str
    github_access_token: str
    remote_opts: CliRemoteOpts

    def __init__(
        self,
        anchor_run_command: str,
        github_organization: str,
        repository_name: str,
        branch_name: str,
        github_access_token: str,
    ) -> None:

        self.anchor_run_command = anchor_run_command
        self.github_organization = github_organization
        self.repository_name = repository_name
        self.branch_name = branch_name
        self.github_access_token = github_access_token
        self.remote_opts = CliRemoteOpts.maybe_get()

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()

        logger.debug(
            f"AnchorCmdArgs: \n"
            + f"  anchor_run_command: {self.node_username}\n"
            + f"  github_organization: {self.github_organization}\n"
            + f"  repository_name: {self.repository_name}\n"
            + f"  branch_name: {self.branch_name}\n"
            + f"  github_access_token: REDACTED\n"
        )


class AnchorCmd:
    def run(self, ctx: Context, args: AnchorCmdArgs) -> None:
        logger.debug("Inside AnchorCmd run()")

        AnchorCmdRunner().run(
            ctx=ctx,
            args=AnchorRunnerCmdArgs(
                anchor_run_command=args.anchor_run_command,
                github_organization=args.github_organization,
                repository_name=args.repository_name,
                branch_name=args.branch_name,
                github_access_token=args.github_access_token,
                remote_opts=args.remote_opts,
            ),
            collaborators=AnchorCmdRunnerCollaborators(ctx),
        )
