#!/usr/bin/env python3

from typing import List, Optional

from loguru import logger
from python_core_lib.errors.cli_errors import MissingCliArgument
from python_core_lib.infra.context import Context
from python_core_lib.infra.evaluator import Evaluator
from python_core_lib.runner.ansible.ansible import HostIpPair
from python_core_lib.shared.collaborators import CoreCollaborators
from python_core_lib.utils.checks import Checks

from provisioner_features_lib.remote.domain.config import RunEnvironment
from provisioner_features_lib.remote.remote_connector import RemoteMachineConnector
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts

# When reading Ansible static files from within `provisioner_features_lib` module, 
# it should be read as relative from the module root folder
AnchorRunAnsiblePlaybookRelativePathFromRoot = "provisioner_features_lib/anchor/playbooks/anchor_run.yaml"

class AnchorRunnerCmdArgs:

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
        remote_opts: Optional[CliRemoteOpts] = None,
    ) -> None:
        self.anchor_run_command = anchor_run_command
        self.github_organization = github_organization
        self.repository_name = repository_name
        self.branch_name = branch_name
        self.github_access_token = github_access_token
        self.remote_opts = remote_opts


class AnchorCmdRunner:
    def run(
        self,
        ctx: Context,
        args: AnchorRunnerCmdArgs,
        collaborators: CoreCollaborators,
    ) -> None:

        logger.debug("Inside AnchorCmdRunner run()")

        self.prerequisites(ctx=ctx, checks=collaborators.checks())

        if args.remote_opts.environment == RunEnvironment.Local:
            self._start_local_run_command_flow(ctx, args, collaborators)
        elif args.remote_opts.environment == RunEnvironment.Remote:
            self._start_remote_run_command_flow(ctx, args, collaborators)
        else:
            raise MissingCliArgument("Missing Cli argument. name: environment")

    def _start_remote_run_command_flow(self, ctx: Context, args: AnchorRunnerCmdArgs, collaborators: CoreCollaborators):

        remote_connector = None
        ssh_conn_info = None
        remote_connector = RemoteMachineConnector(
            collaborators.checks(), collaborators.printer(), collaborators.prompter(), collaborators.network_util()
        )
        ssh_conn_info = Evaluator.eval_step_return_failure_throws(
            call=lambda: remote_connector.collect_ssh_connection_info(ctx, args.remote_opts),
            ctx=ctx,
            err_msg="Could not resolve SSH connection info",
        )
        collaborators.summary().add_values("ssh_conn_info", ssh_conn_info)

        ansible_vars = [
            "anchor_command=Run",
            f"\"anchor_args='{args.anchor_run_command}'\"",
            f"anchor_github_organization={args.github_organization}",
            f"anchor_github_repository={args.repository_name}",
            f"anchor_github_repo_branch={args.branch_name}",
            f"github_access_token={args.github_access_token}",
        ]

        collaborators.printer().new_line_fn()

        output = collaborators.printer().progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.ansible_runner().run_fn(
                working_dir=collaborators.io_utils().get_path_from_exec_module_root_fn(),
                username=ssh_conn_info.username,
                password=ssh_conn_info.password,
                ssh_private_key_file_path=ssh_conn_info.ssh_private_key_file_path,
                playbook_path=collaborators.io_utils().get_path_relative_from_module_root_fn(__name__, AnchorRunAnsiblePlaybookRelativePathFromRoot),
                extra_modules_paths=[collaborators.io_utils().get_path_abs_to_module_root_fn(__name__)],
                ansible_vars=ansible_vars,
                ansible_tags=["ansible_run"],
                selected_hosts=ssh_conn_info.host_ip_pairs,
            ),
            desc_run="Running Ansible playbook (Anchor Run)",
            desc_end="Ansible playbook finished (Anchor Run).",
        )

        collaborators.printer().new_line_fn()
        collaborators.printer().print_fn(output)
        collaborators.printer().print_with_rich_table_fn(
            generate_summary(
                host_ip_pairs=ssh_conn_info.host_ip_pairs,
                anchor_cmd=args.anchor_run_command,
            )
        )

    def _start_local_run_command_flow(self, ctx: Context, args: AnchorRunnerCmdArgs, collaborators: CoreCollaborators):
        output = collaborators.process().run_fn([f"anchor {args.anchor_run_command}"], allow_single_shell_command_str=True)
        collaborators.printer().print_fn(output)

    def prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_darwin():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")


def generate_summary(host_ip_pairs: List[HostIpPair], anchor_cmd: str):
    host_names = []
    ip_addresses = []
    if host_ip_pairs and len(host_ip_pairs) > 0:
        for pair in host_ip_pairs:
            host_names.append(pair.host)
            ip_addresses.append(pair.ip_address)
    return f"""
  You have successfully ran an Anchor command on the following remote machines:
  
    • Host Names.....: [yellow]{host_names}[/yellow]
    • IP Addresses...: [yellow]{ip_addresses}[/yellow]
    • Command........: [yellow]anchor {anchor_cmd}[/yellow]
"""
