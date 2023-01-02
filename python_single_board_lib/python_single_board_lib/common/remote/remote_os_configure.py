#!/usr/bin/env python3

from loguru import logger
from python_core_lib.infra.context import Context
from python_core_lib.infra.evaluator import Evaluator
from python_core_lib.shared.collaborators import CoreCollaborators
from python_core_lib.utils.checks import Checks
from python_core_lib.utils.printer import Printer
from python_core_lib.utils.prompter import Prompter

from python_features_lib.remote.remote_connector import (
    RemoteMachineConnector,
    SSHConnectionInfo,
)
from python_features_lib.remote.typer_remote_opts import CliRemoteOpts


class RemoteMachineOsConfigureArgs:

    ansible_playbook_relative_path_from_root: str
    remote_opts: CliRemoteOpts

    def __init__(self, remote_opts: CliRemoteOpts, ansible_playbook_relative_path_from_root: str) -> None:
        self.remote_opts = remote_opts
        self.ansible_playbook_relative_path_from_root = ansible_playbook_relative_path_from_root

class RemoteMachineOsConfigureRunner:
    def run(self, ctx: Context, args: RemoteMachineOsConfigureArgs, collaborators: CoreCollaborators) -> None:
        logger.debug("Inside RemoteMachineOsConfigureRunner run()")

        self.prerequisites(ctx=ctx, checks=collaborators.__checks)
        self._print_pre_run_instructions(collaborators.__printer, collaborators.__prompter)

        remote_connector = RemoteMachineConnector(
            collaborators.__checks, collaborators.__printer, collaborators.__prompter, collaborators.__network_util
        )

        ssh_conn_info = Evaluator.eval_step_return_failure_throws(
            call=lambda: remote_connector.collect_ssh_connection_info(
                ctx, args.remote_opts, force_single_conn_info=True
            ),
            ctx=ctx,
            err_msg="Could not resolve SSH connection info",
        )
        collaborators.__summary.add_values("ssh_conn_info", ssh_conn_info)

        hostname_ip_tuple = self._extract_host_ip_tuple(ctx, ssh_conn_info)
        ssh_hostname = hostname_ip_tuple[0]
        ssh_ip_address = hostname_ip_tuple[1]
        ansible_vars = [f"host_name={ssh_hostname}"]

        collaborators.__summary.show_summary_and_prompt_for_enter("Configure OS")

        output = collaborators.__printer.progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.ansible_runner().run_fn(
                working_dir=collaborators.io_utils().get_path_from_exec_module_root_fn(),
                username=ssh_conn_info.username,
                password=ssh_conn_info.password,
                ssh_private_key_file_path=ssh_conn_info.ssh_private_key_file_path,
                playbook_path=collaborators.io_utils().get_path_relative_from_module_root_fn(__name__, args.ansible_playbook_relative_path_from_root),
                extra_modules_paths=[collaborators.io_utils().get_path_abs_to_module_root_fn(__name__)],
                ansible_vars=ansible_vars,
                ansible_tags=["configure_remote_node", "reboot"],
                selected_hosts=ssh_conn_info.host_ip_pairs,
            ),
            desc_run="Running Ansible playbook (Configure OS)",
            desc_end="Ansible playbook finished (Configure OS).",
        )

        collaborators.__printer.new_line_fn()
        collaborators.__printer.print_fn(output)
        collaborators.__printer.print_with_rich_table_fn(
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

    def prerequisites(self, ctx: Context, checks: Checks) -> None:
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
