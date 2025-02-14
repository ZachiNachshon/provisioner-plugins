#!/usr/bin/env python3

from typing import Callable

from loguru import logger

from provisioner_shared.components.remote.remote_connector import SSHConnectionInfo
from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.runner.ansible.ansible_runner import AnsibleHost, AnsiblePlaybook
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
        self._run_ansible_hello_playbook_with_progress_bar(
            get_ssh_conn_info_fn=self._get_ssh_conn_info,
            collaborators=collaborators,
            args=args,
        )

    def _get_ssh_conn_info(self) -> SSHConnectionInfo:
        # return SSHConnectionInfo(
        #     ansible_hosts=[
        #         AnsibleHost(
        #             host="test",
        #             ip_address="1.1.1.1",
        #             username="pi",
        #             password="raspbian",
        #         )
        #     ]
        # )
        return SSHConnectionInfo(
            ansible_hosts=[
                AnsibleHost(
                    host="localhost",
                    ip_address="ansible_connection=local",
                    username="pi",
                    # password="raspbian",
                )
            ]
        )

    def _run_ansible_hello_playbook_with_progress_bar(
        self,
        get_ssh_conn_info_fn: Callable[..., SSHConnectionInfo],
        collaborators: CoreCollaborators,
        args: HelloWorldRunnerArgs,
    ) -> str:

        ssh_conn_info = get_ssh_conn_info_fn()
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
