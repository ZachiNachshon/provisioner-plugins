#!/usr/bin/env python3

from typing import Optional

from loguru import logger
from python_core_lib.infra.context import Context

from python_features_lib.anchor.anchor_runner import (
    AnchorCmdRunner,
    AnchorCmdRunnerCollaborators,
    AnchorRunnerCmdArgs,
)
from python_features_lib.remote.remote_connector import RemoteCliArgs


class AnchorCmdArgs(RemoteCliArgs):

    anchor_run_command: str
    github_organization: str
    repository_name: str
    branch_name: str
    github_access_token: str

    def __init__(
        self,
        anchor_run_command: str,
        github_organization: str,
        repository_name: str,
        branch_name: str,
        github_access_token: str,
        node_username: Optional[str] = None,
        node_password: Optional[str] = None,
        ip_discovery_range: Optional[str] = None,
    ) -> None:

        super().__init__(node_username, node_password, ip_discovery_range)
        self.anchor_run_command = anchor_run_command
        self.github_organization = github_organization
        self.repository_name = repository_name
        self.branch_name = branch_name
        self.github_access_token = github_access_token

    def print(self) -> None:
        super().print()
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
                node_username=args.node_username,
                node_password=args.node_password,
                ip_discovery_range=args.ip_discovery_range,
                anchor_run_command=args.anchor_run_command,
                github_organization=args.github_organization,
                repository_name=args.repository_name,
                branch_name=args.branch_name,
                github_access_token=args.github_access_token,
            ),
            collaborators=AnchorCmdRunnerCollaborators(ctx),
        )
