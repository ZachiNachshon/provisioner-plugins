#!/usr/bin/env python3

from loguru import logger
from provisioner_features_lib.remote.remote_connector import (
    RemoteMachineConnector,
    SSHConnectionInfo,
)
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.infra.context import Context
from python_core_lib.infra.evaluator import Evaluator
from python_core_lib.shared.collaborators import CoreCollaborators
from python_core_lib.utils.checks import Checks
from python_core_lib.utils.printer import Printer
from python_core_lib.utils.prompter import Prompter


class RemoteMachineOsConfigureArgs:

    ansible_playbook_relative_path_from_root: str
    remote_opts: CliRemoteOpts

    def __init__(self, remote_opts: CliRemoteOpts, ansible_playbook_relative_path_from_root: str) -> None:
        self.remote_opts = remote_opts
        self.ansible_playbook_relative_path_from_root = ansible_playbook_relative_path_from_root


class RemoteMachineOsConfigureRunner:
    def run(self, ctx: Context, args: RemoteMachineOsConfigureArgs, collaborators: CoreCollaborators) -> None:
        logger.debug("Inside RemoteMachineOsConfigureRunner run()")

        self._prerequisites(ctx=ctx, checks=collaborators.checks())
        self._print_pre_run_instructions(collaborators.printer(), collaborators.prompter()),

        ssh_conn_info = Evaluator.eval_step_return_failure_throws(
            call=lambda: RemoteMachineConnector(collaborators=collaborators).collect_ssh_connection_info(
                ctx, args.remote_opts, force_single_conn_info=True
            ),
            ctx=ctx,
            err_msg="Could not resolve SSH connection info",
        )
        collaborators.summary().append("ssh_conn_info", ssh_conn_info)

        hostname_ip_tuple = self._extract_host_ip_tuple(ctx, ssh_conn_info)
        ssh_hostname = hostname_ip_tuple[0]
        ssh_ip_address = hostname_ip_tuple[1]

        collaborators.summary().show_summary_and_prompt_for_enter("Configure OS")

        output = collaborators.printer().progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.ansible_runner().run_fn(
                working_dir=collaborators.paths().get_path_from_exec_module_root_fn(),
                username=ssh_conn_info.username,
                password=ssh_conn_info.password,
                ssh_private_key_file_path=ssh_conn_info.ssh_private_key_file_path,
                playbook_path=collaborators.paths().get_path_relative_from_module_root_fn(
                    __name__, args.ansible_playbook_relative_path_from_root
                ),
                extra_modules_paths=[collaborators.paths().get_path_abs_to_module_root_fn(__name__)],
                ansible_vars=[f"host_name={ssh_hostname}"],
                ansible_tags=["configure_remote_node", "reboot"],
                selected_hosts=ssh_conn_info.host_ip_pairs,
            ),
            desc_run="Running Ansible playbook (Configure OS)",
            desc_end="Ansible playbook finished (Configure OS).",
        )

        collaborators.printer().new_line_fn()
        collaborators.printer().print_fn(output)
        collaborators.printer().print_with_rich_table_fn(
            generate_instructions_post_configure(hostname=ssh_hostname, ip_address=ssh_ip_address)
        )

    def _extract_host_ip_tuple(self, ctx: Context, ssh_conn_info: SSHConnectionInfo) -> tuple[str, str]:
        if ctx.is_dry_run():
            return ("DRY_RUN_RESPONSE", "DRY_RUN_RESPONSE")
        else:
            # Promised to have only single item
            single_pair_item = ssh_conn_info.host_ip_pairs[0]
            return (single_pair_item.host, single_pair_item.ip_address)

    def _print_pre_run_instructions(self, printer: Printer, prompter: Prompter):
        printer.print_fn(generate_logo_configure())
        printer.print_with_rich_table_fn(generate_instructions_pre_configure())
        prompter.prompt_for_enter_fn()

    def _prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_darwin():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")


def generate_logo_configure() -> str:
    return f"""
 ██████╗ ███████╗     ██████╗ ██████╗ ███╗   ██╗███████╗██╗ ██████╗ ██╗   ██╗██████╗ ███████╗
██╔═══██╗██╔════╝    ██╔════╝██╔═══██╗████╗  ██║██╔════╝██║██╔════╝ ██║   ██║██╔══██╗██╔════╝
██║   ██║███████╗    ██║     ██║   ██║██╔██╗ ██║█████╗  ██║██║  ███╗██║   ██║██████╔╝█████╗
██║   ██║╚════██║    ██║     ██║   ██║██║╚██╗██║██╔══╝  ██║██║   ██║██║   ██║██╔══██╗██╔══╝
╚██████╔╝███████║    ╚██████╗╚██████╔╝██║ ╚████║██║     ██║╚██████╔╝╚██████╔╝██║  ██║███████╗
 ╚═════╝ ╚══════╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝
"""


def generate_instructions_pre_configure() -> str:
    return f"""
  Select a remote Raspberry Pi node to configure Raspbian OS software and hardware settings.
  Configuration is aimed for an optimal headless Raspberry Pi used as a Kubernetes cluster node.

  Complete the following steps:
    1. Eject the SD-Card
    2. Connect the SD-Card to a Raspberry Pi node
    3. Connect the Raspberry Pi node to a power supply
    4. Connect the Raspberry Pi node to the network
"""


def generate_instructions_post_configure(hostname: str, ip_address: str):
    return f"""
  You have successfully configured hardware and system settings for a Raspberry Pi node:
  
    • Host Name....: [yellow]{hostname}[/yellow]
    • IP Address...: [yellow]{ip_address}[/yellow]
"""
