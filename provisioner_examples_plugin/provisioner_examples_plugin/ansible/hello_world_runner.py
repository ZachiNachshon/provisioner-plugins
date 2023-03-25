#!/usr/bin/env python3

from typing import Callable

from loguru import logger
from provisioner_features_lib.remote.remote_connector import SSHConnectionInfo
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.infra.context import Context
from python_core_lib.runner.ansible.ansible import AnsibleHost, AnsibleRunner
from python_core_lib.shared.collaborators import CoreCollaborators
from python_core_lib.utils.checks import Checks
from python_core_lib.utils.printer import Printer
from python_core_lib.utils.prompter import Prompter


class HelloWorldRunnerArgs:

    username: str
    ansible_playbook_relative_path_from_module: str
    remote_opts: CliRemoteOpts

    def __init__(
        self, username: str, ansible_playbook_relative_path_from_module: str, remote_opts: CliRemoteOpts
    ) -> None:
        self.username = username
        self.ansible_playbook_relative_path_from_module = ansible_playbook_relative_path_from_module
        self.remote_opts = remote_opts


class HelloWorldRunner:
    def run(self, ctx: Context, args: HelloWorldRunnerArgs, collaborators: CoreCollaborators) -> None:
        logger.debug("Inside HelloWorldRunner run()")

        self._prerequisites(ctx=ctx, checks=collaborators.checks())
        self._print_pre_run_instructions(collaborators.printer(), collaborators.prompter())
        self._run_ansible_hello_playbook_with_progress_bar(
            get_ssh_conn_info_fn=self._get_ssh_conn_info, collaborators=collaborators, args=args
        )

    def _get_ssh_conn_info(self) -> SSHConnectionInfo:
        return SSHConnectionInfo(
            ansible_hosts=[
                AnsibleHost(
                    host="localhost",
                    ip_address="ansible_connection=local",
                    username="pi",
                    password="raspbian",
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
        output = collaborators.printer().progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.ansible_runner().run_fn(
                selected_hosts=ssh_conn_info.ansible_hosts,
                with_paths=AnsibleRunner.WithPaths.create(
                    paths=collaborators.paths(),
                    script_import_name_var=__name__,
                    playbook_path=args.ansible_playbook_relative_path_from_module,
                ),
                ansible_vars=[f"\"username='{args.username}'\""],
                ansible_tags=["hello"],
            ),
            desc_run="Running Ansible playbook (Hello World)",
            desc_end="Ansible playbook finished (Hello World).",
        )
        collaborators.printer().new_line_fn().print_fn(output)

    def _print_pre_run_instructions(self, printer: Printer, prompter: Prompter):
        printer.print_horizontal_line_fn(message="Running 'Hello World' via Ansible local connection")
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
