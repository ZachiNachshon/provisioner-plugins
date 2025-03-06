#!/usr/bin/env python3

from loguru import logger

from provisioner_shared.components.remote.remote_connector import RemoteMachineConnector, SSHConnectionInfo
from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.runner.ansible.ansible_runner import AnsiblePlaybook
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.runtime.utils.checks import Checks
from provisioner_shared.components.runtime.utils.printer import Printer
from provisioner_shared.components.runtime.utils.prompter import Prompter

ANSIBLE_PLAYBOOK_HELLO_WORLD = """
---
- name: Hello World Run
  hosts: selected_hosts
  gather_facts: no
  {modifiers}

  roles:
    - role: {ansible_playbooks_path}/roles/hello_world
      tags: ['hello']
"""


class HelloWorldRunnerArgs:

    username: str
    remote_opts: RemoteOpts

    def __init__(self, username: str, remote_opts: RemoteOpts) -> None:
        self.username = username
        self.remote_opts = remote_opts


class HelloWorldRunner:
    def run(self, ctx: Context, args: HelloWorldRunnerArgs, collaborators: CoreCollaborators) -> None:
        logger.debug("Inside HelloWorldRunner run()")

        self._prerequisites(ctx=ctx, checks=collaborators.checks())
        self._print_pre_run_instructions(collaborators.printer(), collaborators.prompter())
        ssh_conn_info = self._get_ssh_conn_info(ctx, collaborators, args.remote_opts)
        self._run_ansible_hello_playbook_with_progress_bar(
            ssh_conn_info=ssh_conn_info,
            collaborators=collaborators,
            args=args,
        )

    def _get_ssh_conn_info(
        self, ctx: Context, collaborators: CoreCollaborators, remote_opts: RemoteOpts
    ) -> SSHConnectionInfo:

        connector = RemoteMachineConnector(collaborators=collaborators)
        ssh_conn_info = connector.collect_ssh_connection_info(
            ctx=ctx, cli_remote_opts=remote_opts, force_single_conn_info=True
        )
        collaborators.summary().append_result(
            attribute_name="ssh_conn_info",
            call=lambda: ssh_conn_info,
        )
        return ssh_conn_info

        # return SSHConnectionInfo(
        #     ansible_hosts=[
        #         AnsibleHost(
        #             host="localhost",
        #             ip_address="ansible_connection=local",
        #             username="pi",
        #             # password="raspbian",
        #         )
        #     ]
        # )

    def _run_ansible_hello_playbook_with_progress_bar(
        self,
        ssh_conn_info: SSHConnectionInfo,
        collaborators: CoreCollaborators,
        args: HelloWorldRunnerArgs,
    ) -> str:

        output = (
            collaborators.progress_indicator()
            .get_status()
            .long_running_process_fn(
                call=lambda: collaborators.ansible_runner().run_fn(
                    selected_hosts=ssh_conn_info.ansible_hosts,
                    playbook=AnsiblePlaybook(
                        name="hello_world",
                        content=ANSIBLE_PLAYBOOK_HELLO_WORLD,
                        remote_context=args.remote_opts.get_remote_context(),
                    ),
                    ansible_vars=[f"username='{args.username}'"],
                    ansible_tags=["hello"],
                ),
                desc_run="Running Ansible playbook (Hello World)",
                desc_end="Ansible playbook finished (Hello World).",
            )
        )
        collaborators.printer().new_line_fn().print_fn(output)

    def _print_pre_run_instructions(self, printer: Printer, prompter: Prompter):
        printer.print_horizontal_line_fn(message="Running 'Hello World' via Ansible local connection")
        prompter.prompt_for_enter_fn()

    def _prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            return
        elif ctx.os_arch.is_darwin():
            return
        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")
