#!/usr/bin/env python3

from typing import List, Optional

from loguru import logger

from provisioner_shared.components.remote.ansible.remote_provisioner_runner import (
    RemoteProvisionerRunner,
    RemoteProvisionerRunnerArgs,
)
from provisioner_shared.components.remote.domain.config import RunEnvironment
from provisioner_shared.components.remote.remote_connector import RemoteMachineConnector, SSHConnectionInfo
from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.infra.evaluator import Evaluator
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.runtime.utils.checks import Checks
from provisioner_shared.components.runtime.utils.system_reader import SystemReader


class SystemInfo:
    os_release: str = ""
    hardware_cpu: str = ""
    hardware_mem: str = ""
    hardware_network: str = ""


class RemoteMachineSystemInfoCollectArgs:
    remote_opts: RemoteOpts

    def __init__(self, remote_opts: RemoteOpts) -> None:
        self.remote_opts = remote_opts


class RemoteMachineSystemInfoCollectRunner:
    class SystemInfoBundle:
        ssh_ip_address: str
        ssh_username: str
        ssh_hostname: str
        static_ip_address: str

        def __init__(self, ssh_ip_address: str, ssh_username: str, ssh_hostname: str, static_ip_address: str) -> None:
            self.ssh_ip_address = ssh_ip_address
            self.ssh_username = ssh_username
            self.ssh_hostname = ssh_hostname
            self.static_ip_address = static_ip_address

    def run(self, ctx: Context, args: RemoteMachineSystemInfoCollectArgs, collaborators: CoreCollaborators) -> None:
        logger.debug("Inside RemoteMachineSystemInfoCollectRunner run()")

        self._prerequisites(ctx=ctx, checks=collaborators.checks())
        if args.remote_opts.get_environment() is not None:
            if args.remote_opts.get_environment() == RunEnvironment.Local:
                system_info = self.collect_system_info(ctx, collaborators)
                collaborators.printer().print_with_rich_table_fn(generate_system_info_summary(system_info))

            elif args.remote_opts.get_environment() == RunEnvironment.Remote:
                ssh_conn_info = self._get_ssh_conn_info(ctx, collaborators, args.remote_opts)
                result = self._collect_system_info_on_remote_machine(ctx, collaborators, args, ssh_conn_info)
                print(result)

            else:
                raise NotImplementedError(
                    f"RunEnvironment enum does not support label '{args.remote_opts.get_environment()}'"
                )

    def _collect_system_info_on_remote_machine(
        self,
        ctx: Context,
        collaborators: CoreCollaborators,
        args: RemoteMachineSystemInfoCollectArgs,
        ssh_conn_info: SSHConnectionInfo,
    ) -> str:
        """Run the system info collection on a remote machine using Ansible."""
        return self._execute_remote_ansible_playbook(
            ctx=ctx,
            args=args,
            collaborators=collaborators,
            ssh_conn_info=ssh_conn_info,
        )

    def _execute_remote_ansible_playbook(
        self,
        ctx: Context,
        args: RemoteMachineSystemInfoCollectArgs,
        collaborators: CoreCollaborators,
        ssh_conn_info: SSHConnectionInfo,
    ) -> str:
        """Execute the Ansible playbook that installs utilities on remote machines."""
        command = self._build_provisioner_command(ctx, args)
        logger.debug(f"Remote provisioner command: {command}")

        ansible_vars = self._prepare_ansible_vars(ctx, args)

        args = RemoteProvisionerRunnerArgs(
            provisioner_command=command,
            remote_context=args.remote_opts.get_remote_context(),
            ssh_connection_info=ssh_conn_info,
            required_plugins=["provisioner_single_board_plugin"],
            ansible_vars=ansible_vars,
        )
        return RemoteProvisionerRunner().run(ctx, args, collaborators)

    def _prepare_ansible_vars(self, ctx: Context, args: RemoteMachineSystemInfoCollectArgs) -> List[str]:
        """Prepare Ansible variables for the remote command."""
        ansible_vars = []
        return ansible_vars

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

    def _build_provisioner_command(self, ctx: Context, args: RemoteMachineSystemInfoCollectArgs) -> str:
        """Build the provisioner command to run on the remote machine."""
        operation = "single-board"
        verbose_flag = "-v" if args.remote_opts.get_remote_context().is_verbose() else ""
        return f"{operation} info --environment Local collect -y {verbose_flag}"

    def collect_system_info(self, ctx: Context, collaborators: CoreCollaborators) -> SystemInfo:
        system_reader = SystemReader(process=collaborators.process(), io_utils=collaborators.io_utils())
        system_info = SystemInfo()
        system_info.os_release = system_reader.read_os_release_func(ctx)
        system_info.hardware_cpu = system_reader.read_hardware_cpu_func(ctx)
        system_info.hardware_mem = system_reader.read_hardware_mem_func(ctx)
        # system_info.hardware_network = system_reader.read_hardware_network_func(ctx)
        return system_info

    def _prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            return
        elif ctx.os_arch.is_darwin():
            return
        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")


def generate_system_info_summary(system_info: SystemInfo) -> str:
    return f"""
[green]OS Release[/green]

  {system_info.os_release}

[green]Hardware CPU[/green]

  {system_info.hardware_cpu}

[green]Hardware Memory[/green]

  {system_info.hardware_mem}

[green]Hardware Network[/green]
  {system_info.hardware_network}
"""
