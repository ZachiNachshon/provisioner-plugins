#!/usr/bin/env python3

from typing import Optional

from loguru import logger

from provisioner_shared.components.remote.remote_connector import (
    RemoteMachineConnector,
    SSHConnectionInfo,
)
from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.infra.evaluator import Evaluator
from provisioner_shared.components.runtime.infra.remote_context import RemoteContext
from provisioner_shared.components.runtime.runner.ansible.ansible_runner import (
    AnsibleHost,
    AnsiblePlaybook,
    AnsibleRunnerLocal,
)
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.runtime.utils.checks import Checks

ANSIBLE_PLAYBOOK_K3S_GATHER_INFO = """
---
- name: Collecting K3s Info on remote RPi host
  hosts: selected_hosts
  gather_facts: no
  {modifiers}

  roles:
    - role: {ansible_playbooks_path}/roles/k3s_gather_info_on_node
      tags: ['k3s_gather_info_on_node']
"""


class RemoteK3sGatherInfoArgs:

    remote_opts: RemoteOpts

    def __init__(self, remote_opts: RemoteOpts) -> None:
        self.remote_opts = remote_opts


class RemoteK3sGatherInfoRunner:

    def run(self, ctx: Context, args: RemoteK3sGatherInfoArgs, collaborators: CoreCollaborators) -> None:
        logger.debug("Inside RemoteK3sGatherInfoRunner run()")

        self._prerequisites(ctx=ctx, checks=collaborators.checks())
        ssh_conn_info = self._get_ssh_conn_info(ctx, collaborators, args.remote_opts)
        ansible_host = self._run_ansible_k3s_gather_info_playbook_with_progress_bar(
            ctx=ctx,
            ssh_conn_info=ssh_conn_info,
            collaborators=collaborators,
            args=args,
        )

    def _run_ansible_k3s_gather_info_playbook_with_progress_bar(
        self,
        ctx: Context,
        ssh_conn_info: SSHConnectionInfo,
        collaborators: CoreCollaborators,
        args: RemoteK3sGatherInfoArgs,
    ) -> AnsibleHost:

        ansible_host = ssh_conn_info.ansible_hosts[0]

        collaborators.summary().show_summary_and_prompt_for_enter("Collecting K3s Info")

        output = (
            collaborators.progress_indicator()
            .get_status()
            .long_running_process_fn(
                call=lambda: self._run_ansible(
                    collaborators.ansible_runner(),
                    args.remote_opts.get_remote_context(),
                    ansible_host.host,
                    ssh_conn_info,
                ),
                desc_run="Running Ansible playbook (K3s Gather Info)",
                desc_end="Ansible playbook finished (K3s Gather Info).",
            )
        )
        collaborators.printer().new_line_fn().print_fn(output)
        return ansible_host

    def _run_ansible(
        self,
        runner: AnsibleRunnerLocal,
        remote_ctx: RemoteContext,
        ssh_hostname: str,
        ssh_conn_info: SSHConnectionInfo,
    ) -> str:

        return runner.run_fn(
            selected_hosts=ssh_conn_info.ansible_hosts,
            playbook=AnsiblePlaybook(
                name="k3s_gather_info_on_node",
                content=ANSIBLE_PLAYBOOK_K3S_GATHER_INFO,
                remote_context=remote_ctx,
            ),
            ansible_vars=[
                f"become_root={'no' if remote_ctx.is_dry_run() else 'yes'}",
            ],
            ansible_tags=["k3s_gather_info_on_node"],
        )

    def _get_ssh_conn_info(
        self, ctx: Context, collaborators: CoreCollaborators, remote_opts: Optional[RemoteOpts] = None
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

    def _prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            return
        elif ctx.os_arch.is_darwin():
            return
        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")
