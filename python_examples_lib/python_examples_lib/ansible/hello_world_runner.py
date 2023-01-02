#!/usr/bin/env python3

from loguru import logger
from python_core_lib.infra.context import Context
from python_core_lib.runner.ansible.ansible import HostIpPair
from python_core_lib.shared.collaborators import CoreCollaborators
from python_core_lib.utils.checks import Checks
from python_core_lib.utils.printer import Printer
from python_core_lib.utils.prompter import Prompter
from python_features_lib.remote.remote_connector import SSHConnectionInfo
from python_features_lib.remote.typer_remote_opts import CliRemoteOpts


class HelloWorldRunnerArgs:

    username: str
    ansible_playbook_relative_path_from_root: str
    remote_opts: CliRemoteOpts

    def __init__(
        self, username: str, ansible_playbook_relative_path_from_root: str, remote_opts: CliRemoteOpts
    ) -> None:
        self.username = username
        self.ansible_playbook_relative_path_from_root = ansible_playbook_relative_path_from_root
        self.remote_opts = remote_opts


class HelloWorldRunner:
    def run(self, ctx: Context, args: HelloWorldRunnerArgs, collaborators: CoreCollaborators) -> None:
        logger.debug("Inside HelloWorldRunner run()")

        self.prerequisites(ctx=ctx, checks=collaborators.__checks)
        self._print_pre_run_instructions(collaborators.__printer, collaborators.__prompter)

        ssh_conn_info = SSHConnectionInfo(
            username="pi",
            password="raspbian",
            host_ip_pairs=[HostIpPair(host="localhost", ip_address="ansible_connection=local")],
        )

        ansible_vars = [f"\"username='{args.username}'\""]

        collaborators.__printer.new_line_fn()

        working_dir = collaborators.__io.get_path_from_exec_module_root_fn()

        output = collaborators.__printer.progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.__ansible_runner.run_fn(
                working_dir=working_dir,
                username=ssh_conn_info.username,
                password=ssh_conn_info.password,
                ssh_private_key_file_path=ssh_conn_info.ssh_private_key_file_path,
                playbook_path=args.ansible_playbook_relative_path_from_root,
                ansible_vars=ansible_vars,
                ansible_tags=["hello"],
                selected_hosts=ssh_conn_info.host_ip_pairs,
            ),
            desc_run="Running Ansible playbook (Hello World)",
            desc_end="Ansible playbook finished (Hello World).",
        )

        collaborators.__printer.new_line_fn()
        collaborators.__printer.print_fn(output)

    def _print_pre_run_instructions(self, printer: Printer, prompter: Prompter):
        printer.print_horizontal_line_fn(message="Running 'Hello World' via Ansible local connection")
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
