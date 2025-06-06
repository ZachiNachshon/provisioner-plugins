#!/usr/bin/env python3

from typing import Optional

from loguru import logger

from provisioner_shared.components.remote.remote_connector import (
    NetworkConfigurationInfo,
    RemoteMachineConnector,
    SSHConnectionInfo,
)
from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.infra.evaluator import Evaluator
from provisioner_shared.components.runtime.infra.remote_context import RemoteContext
from provisioner_shared.components.runtime.runner.ansible.ansible_runner import AnsiblePlaybook, AnsibleRunnerLocal
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.runtime.utils.checks import Checks

ANSIBLE_PLAYBOOK_RPI_CONFIGURE_NETWORK = """
---
- name: Configure static IP address and hostname on remote RPi host
  hosts: selected_hosts
  gather_facts: no
  {modifiers}

  roles:
    - role: {ansible_playbooks_path}/roles/rpi_config_network
      tags: ['configure_rpi_network']

    - role: {ansible_playbooks_path}/roles/dhcp_static_ip
      tags: ['define_static_ip']
"""


class RemoteMachineNetworkConfigureArgs:
    gw_ip_address: str
    dns_ip_address: str
    static_ip_address: str
    remote_opts: RemoteOpts
    update_hosts_file: bool

    def __init__(
        self,
        gw_ip_address: str,
        dns_ip_address: str,
        static_ip_address: str,
        remote_opts: RemoteOpts,
        update_hosts_file: bool = False,
    ) -> None:
        self.gw_ip_address = gw_ip_address
        self.dns_ip_address = dns_ip_address
        self.static_ip_address = static_ip_address
        self.remote_opts = remote_opts
        self.update_hosts_file = update_hosts_file


class RemoteMachineNetworkConfigureRunner:
    class NetworkInfoBundle:
        ssh_ip_address: str
        ssh_username: str
        ssh_hostname: str
        static_ip_address: str

        def __init__(self, ssh_ip_address: str, ssh_username: str, ssh_hostname: str, static_ip_address: str) -> None:
            self.ssh_ip_address = ssh_ip_address
            self.ssh_username = ssh_username
            self.ssh_hostname = ssh_hostname
            self.static_ip_address = static_ip_address

    def run(self, ctx: Context, args: RemoteMachineNetworkConfigureArgs, collaborators: CoreCollaborators) -> None:
        logger.debug("Inside RemoteMachineNetworkConfigureRunner run()")

        self._prerequisites(ctx=ctx, checks=collaborators.checks())
        self._print_pre_run_instructions(collaborators)
        ssh_conn_info = self._get_ssh_conn_info(ctx, collaborators, args.remote_opts)
        network_configure_info = self._get_network_configure_info(ctx, collaborators, args, ssh_conn_info)

        tuple_info = self._run_ansible_network_configure_playbook_with_progress_bar(
            ctx=ctx,
            ssh_conn_info=ssh_conn_info,
            network_configure_info=network_configure_info,
            collaborators=collaborators,
            args=args,
        )
        self._print_post_run_instructions(ctx, tuple_info, collaborators)
        self._maybe_add_hosts_file_entry(ctx, tuple_info, collaborators, args.update_hosts_file)

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

    def _get_network_configure_info(
        self,
        ctx: Context,
        collaborators: CoreCollaborators,
        args: RemoteMachineNetworkConfigureArgs,
        ssh_conn_info: SSHConnectionInfo,
    ) -> NetworkConfigurationInfo:

        network_configure_info = Evaluator.eval_step_return_value_throw_on_failure(
            call=lambda: RemoteMachineConnector(collaborators=collaborators).collect_network_configuration_info(
                ctx=ctx,
                ansible_hosts=ssh_conn_info.ansible_hosts,
                static_ip_address=args.static_ip_address,
                gw_ip_address=args.gw_ip_address,
                dns_ip_address=args.dns_ip_address,
            ),
            ctx=ctx,
            err_msg="Could not resolve network configuration info",
        )
        collaborators.summary().append("network_configure_info", network_configure_info)
        return network_configure_info

    def _run_ansible_network_configure_playbook_with_progress_bar(
        self,
        ctx: Context,
        ssh_conn_info: SSHConnectionInfo,
        network_configure_info: NetworkConfigurationInfo,
        collaborators: CoreCollaborators,
        args: RemoteMachineNetworkConfigureArgs,
    ) -> tuple[SSHConnectionInfo, NetworkConfigurationInfo]:

        tuple_info = (ssh_conn_info, network_configure_info)
        network_info = self._bundle_network_information_from_tuple(ctx, tuple_info)
        collaborators.summary().show_summary_and_prompt_for_enter("Configure Network")
        output = (
            collaborators.progress_indicator()
            .get_status()
            .long_running_process_fn(
                call=lambda: self._run_ansible(
                    collaborators.ansible_runner(),
                    args.remote_opts.get_remote_context(),
                    network_info.ssh_hostname,
                    ssh_conn_info,
                    network_configure_info,
                ),
                desc_run="Running Ansible playbook (Configure Network)",
                desc_end="Ansible playbook finished (Configure Network).",
            )
        )
        collaborators.printer().new_line_fn().print_fn(output)
        return tuple_info

    def _run_ansible(
        self,
        runner: AnsibleRunnerLocal,
        remote_ctx: RemoteContext,
        ssh_hostname: str,
        ssh_conn_info: SSHConnectionInfo,
        network_configure_info: NetworkConfigurationInfo,
    ) -> str:

        return runner.run_fn(
            selected_hosts=ssh_conn_info.ansible_hosts,
            playbook=AnsiblePlaybook(
                name="rpi_configure_network",
                content=ANSIBLE_PLAYBOOK_RPI_CONFIGURE_NETWORK,
                remote_context=remote_ctx,
            ),
            ansible_vars=[
                f"host_name={ssh_hostname}",
                f"static_ip={network_configure_info.static_ip_address}",
                f"gateway_address={network_configure_info.gw_ip_address}",
                f"dns_address={network_configure_info.dns_ip_address}",
                f"become_root={'no' if remote_ctx.is_dry_run() else 'yes'}",
                f"reboot_required={'false' if remote_ctx.is_dry_run() else 'true'}",
            ],
            ansible_tags=[
                "configure_rpi_network",
                "define_static_ip",
            ]
            + (["reboot"] if not remote_ctx.is_dry_run() else []),
        )

    def _print_post_run_instructions(
        self,
        ctx: Context,
        tuple_info: tuple[SSHConnectionInfo, NetworkConfigurationInfo],
        collaborators: CoreCollaborators,
    ):
        network_info = self._bundle_network_information_from_tuple(ctx, tuple_info)
        collaborators.printer().print_with_rich_table_fn(
            generate_instructions_post_network(
                username=network_info.ssh_username,
                hostname=network_info.ssh_hostname,
                ip_address=network_info.ssh_ip_address,
                static_ip=network_info.static_ip_address,
            )
        )

    def _extract_host_ip_tuple(self, ctx: Context, ssh_conn_info: SSHConnectionInfo) -> tuple[str, str]:
        if ctx.is_dry_run():
            return ("DRY_RUN_RESPONSE", "DRY_RUN_RESPONSE")
        else:
            # Promised to have only single item
            single_pair_item = ssh_conn_info.ansible_hosts[0]
            return (single_pair_item.host, single_pair_item.ip_address)

    def _maybe_add_hosts_file_entry(
        self,
        ctx: Context,
        tuple_info: tuple[SSHConnectionInfo, NetworkConfigurationInfo],
        collaborators: CoreCollaborators,
        update_hosts_file: bool,
    ):
        """Add entry to hosts file if needed."""
        if not update_hosts_file:
            collaborators.printer().print_fn("Skipping hosts file update as --update-hosts-file flag was not specified")
            return

        collaborators.printer().print_fn(
            "Updating hosts file with the remote IP address and hostname (Password required)\n"
        )
        network_info = self._bundle_network_information_from_tuple(ctx, tuple_info)
        collaborators.hosts_file().add_entry_fn(
            ip_address=network_info.static_ip_address,
            dns_names=[network_info.ssh_hostname],
            comment=f"Added by provisioner for {network_info.ssh_hostname}",
        )

    def _print_pre_run_instructions(self, collaborators: CoreCollaborators):
        collaborators.printer().print_fn(generate_logo_network())
        collaborators.printer().print_with_rich_table_fn(generate_instructions_pre_network())
        collaborators.prompter().prompt_for_enter_fn()

    def _bundle_network_information_from_tuple(
        self, ctx: Context, tuple_info: tuple[SSHConnectionInfo, NetworkConfigurationInfo]
    ) -> "RemoteMachineNetworkConfigureRunner.NetworkInfoBundle":
        ssh_conn_info = tuple_info[0]
        ansible_host = ssh_conn_info.ansible_hosts[0]

        network_configure_info = tuple_info[1]
        static_ip_address = network_configure_info.static_ip_address

        return RemoteMachineNetworkConfigureRunner.NetworkInfoBundle(
            ssh_username=ansible_host.username,
            ssh_hostname=ansible_host.host,
            ssh_ip_address=ansible_host.ip_address,
            static_ip_address=static_ip_address,
        )

    def _prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            return
        elif ctx.os_arch.is_darwin():
            return
        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")


def generate_logo_network() -> str:
    return """
 ██████╗ ███████╗    ███╗   ██╗███████╗████████╗██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗
██╔═══██╗██╔════╝    ████╗  ██║██╔════╝╚══██╔══╝██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝
██║   ██║███████╗    ██╔██╗ ██║█████╗     ██║   ██║ █╗ ██║██║   ██║██████╔╝█████╔╝
██║   ██║╚════██║    ██║╚██╗██║██╔══╝     ██║   ██║███╗██║██║   ██║██╔══██╗██╔═██╗
╚██████╔╝███████║    ██║ ╚████║███████╗   ██║   ╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗
 ╚═════╝ ╚══════╝    ╚═╝  ╚═══╝╚══════╝   ╚═╝    ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝"""


def generate_instructions_pre_network() -> str:
    return """
  Select a remote Raspberry Pi node ([yellow]ethernet connected[/yellow]) to set a static IP address.
  It uses nmcli (NetworkManager Command Line Tool) to set the static IP address.

  It is vital for a RPi server to have a predictable address to interact with.
  Every time the Raspberry Pi node will connect to the network, it will use the same address.
"""


def generate_instructions_post_network(ip_address: str, static_ip: str, username: str, hostname: str):
    return f"""
  [green]Congratulations ![/green]

  You have successfully set a static IP for a Raspberry Pi node:
    • [yellow]{ip_address}[/yellow] --> [yellow]{static_ip}[/yellow]

  To update the node password:
    • SSH into the node - [yellow]ssh {username}@{static_ip}[/yellow]
                          [yellow]ssh {username}@{hostname}[/yellow]
    • Update password   - [yellow]sudo /usr/bin/raspi-config nonint do_change_pass[/yellow]

  To declare the new static node in the provisioner config,
  update the following file ~/.config/provisioner/config.yaml with:

    <plugin-name>:
      remote:
        hosts:
        - name: <NAME>
          address: <IP-ADDRESS>
          auth:
            username: <USERNAME>
            ssh_private_key_file_path: <PATH-TO-PRIVATE-KEY> (recommended)
            password: <PASSWORD> (optional)
"""
