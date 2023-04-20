#!/usr/bin/env python3

from typing import Callable, Optional

from loguru import logger
from provisioner_features_lib.remote.remote_connector import (
    RemoteMachineConnector,
    SSHConnectionInfo,
)
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.infra.context import Context
from python_core_lib.infra.evaluator import Evaluator
from python_core_lib.runner.ansible.ansible_runner import (
    AnsibleHost,
    AnsiblePlaybook,
    AnsibleRunnerLocal,
)
from python_core_lib.shared.collaborators import CoreCollaborators
from python_core_lib.utils.checks import Checks

ANSIBLE_PLAYBOOK_RPI_CONFIGURE_NODE = """
---
- name: Configure Raspbian OS on remote RPi host
  hosts: selected_hosts
  gather_facts: no
  {modifiers}
  roles:
    - role: {ansible_playbooks_path}/roles/rpi_config_node
      tags: ['configure_remote_node']

  tasks:
    - name: Reboot and wait
      include_tasks: {ansible_playbooks_path}/reboot.yaml
      tags: ['reboot'] 
"""


class RemoteMachineOsConfigureArgs:

    remote_opts: CliRemoteOpts

    def __init__(self, remote_opts: CliRemoteOpts) -> None:
        self.remote_opts = remote_opts


class RemoteMachineOsConfigureRunner:
    def run(self, ctx: Context, args: RemoteMachineOsConfigureArgs, collaborators: CoreCollaborators) -> None:
        logger.debug("Inside RemoteMachineOsConfigureRunner run()")

        self._prerequisites(ctx=ctx, checks=collaborators.checks())
        self._print_pre_run_instructions(collaborators),
        ansible_host = self._run_ansible_configure_os_playbook_with_progress_bar(
            ctx=ctx,
            get_ssh_conn_info_fn=self._get_ssh_conn_info,
            collaborators=collaborators,
            args=args,
        )
        self._print_post_run_instructions(ansible_host, collaborators)

    def _run_ansible_configure_os_playbook_with_progress_bar(
        self,
        ctx: Context,
        get_ssh_conn_info_fn: Callable[..., SSHConnectionInfo],
        collaborators: CoreCollaborators,
        args: RemoteMachineOsConfigureArgs,
    ) -> AnsibleHost:

        ssh_conn_info = get_ssh_conn_info_fn(ctx, collaborators, args.remote_opts)
        ansible_host = ssh_conn_info.ansible_hosts[0]

        collaborators.summary().show_summary_and_prompt_for_enter("Configure OS")

        output = collaborators.printer().progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.ansible_runner().run_fn(
                selected_hosts=ssh_conn_info.ansible_hosts,
                playbook=AnsiblePlaybook(name="rpi_configure_node", content=ANSIBLE_PLAYBOOK_RPI_CONFIGURE_NODE),
                ansible_vars=[f"host_name={ansible_host.host}"],
                ansible_tags=["configure_remote_node", "reboot"],
            ),
            desc_run="Running Ansible playbook (Configure OS)",
            desc_end="Ansible playbook finished (Configure OS).",
        )
        collaborators.printer().new_line_fn().print_fn(output)
        return ansible_host

    def _get_ssh_conn_info(
        self, ctx: Context, collaborators: CoreCollaborators, remote_opts: Optional[CliRemoteOpts] = None
    ) -> SSHConnectionInfo:

        ssh_conn_info = Evaluator.eval_step_return_value_throw_on_failure(
            call=lambda: RemoteMachineConnector(collaborators=collaborators).collect_ssh_connection_info(
                ctx, remote_opts, force_single_conn_info=True
            ),
            ctx=ctx,
            err_msg="Could not resolve SSH connection info",
        )
        collaborators.summary().append("ssh_conn_info", ssh_conn_info)
        return ssh_conn_info

    def _print_pre_run_instructions(self, collaborators: CoreCollaborators):
        collaborators.printer().print_fn(generate_logo_configure())
        collaborators.printer().print_with_rich_table_fn(generate_instructions_pre_configure())
        collaborators.prompter().prompt_for_enter_fn()

    def _print_post_run_instructions(
        self,
        ansible_host: AnsibleHost,
        collaborators: CoreCollaborators,
    ):
        collaborators.printer().print_with_rich_table_fn(generate_instructions_post_configure(ansible_host))

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


def generate_instructions_post_configure(ansible_host: AnsibleHost):
    return f"""
  You have successfully configured hardware and system settings for a Raspberry Pi node:
  
    • Host Name....: [yellow]{ansible_host.host}[/yellow]
    • IP Address...: [yellow]{ansible_host.ip_address}[/yellow]
"""
