#!/usr/bin/env python3

from typing import Callable, Optional

from loguru import logger
from provisioner_features_lib.remote.remote_connector import (
    DHCPCDConfigurationInfo,
    RemoteMachineConnector,
    SSHConnectionInfo,
)
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.colors import color
from python_core_lib.infra.context import Context
from python_core_lib.infra.evaluator import Evaluator
from python_core_lib.shared.collaborators import CoreCollaborators
from python_core_lib.utils.checks import Checks


class RemoteMachineNetworkConfigureArgs:
    gw_ip_address: str
    dns_ip_address: str
    static_ip_address: str
    ansible_playbook_relative_path_from_root: str
    remote_opts: CliRemoteOpts

    def __init__(
        self,
        gw_ip_address: str,
        dns_ip_address: str,
        static_ip_address: str,
        ansible_playbook_relative_path_from_root: str,
        remote_opts: CliRemoteOpts,
    ) -> None:
        self.gw_ip_address = gw_ip_address
        self.dns_ip_address = dns_ip_address
        self.static_ip_address = static_ip_address
        self.ansible_playbook_relative_path_from_root = ansible_playbook_relative_path_from_root
        self.remote_opts = remote_opts


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
        tuple_info = self._run_ansible_network_configure_playbook_with_progress_bar(
            ctx=ctx,
            get_ssh_conn_info_fn=self._get_ssh_conn_info,
            get_dhcpcd_configure_info_fn=self._get_dhcpcd_configure_info,
            collaborators=collaborators,
            args=args,
        )
        self._print_post_run_instructions(ctx, tuple_info, collaborators)
        self._maybe_add_hosts_file_entry(ctx, tuple_info, collaborators)

    def _get_ssh_conn_info(
        self, ctx: Context, collaborators: CoreCollaborators, remote_opts: Optional[CliRemoteOpts] = None
    ) -> SSHConnectionInfo:

        ssh_conn_info = Evaluator.eval_step_return_failure_throws(
            call=lambda: RemoteMachineConnector(collaborators=collaborators).collect_ssh_connection_info(
                ctx, remote_opts, force_single_conn_info=True
            ),
            ctx=ctx,
            err_msg="Could not resolve SSH connection info",
        )
        collaborators.summary().append("ssh_conn_info", ssh_conn_info)
        return ssh_conn_info

    def _get_dhcpcd_configure_info(
        self,
        ctx: Context,
        collaborators: CoreCollaborators,
        args: RemoteMachineNetworkConfigureArgs,
        ssh_conn_info: SSHConnectionInfo,
    ) -> DHCPCDConfigurationInfo:

        dhcpcd_configure_info = Evaluator.eval_step_return_failure_throws(
            call=lambda: RemoteMachineConnector(collaborators=collaborators).collect_dhcpcd_configuration_info(
                ctx=ctx,
                host_ip_pairs=ssh_conn_info.host_ip_pairs,
                static_ip_address=args.static_ip_address,
                gw_ip_address=args.gw_ip_address,
                dns_ip_address=args.dns_ip_address,
            ),
            ctx=ctx,
            err_msg="Could not resolve SSH connection info",
        )
        collaborators.summary().append("dhcpcd_configure_info", dhcpcd_configure_info)
        return dhcpcd_configure_info

    def _run_ansible_network_configure_playbook_with_progress_bar(
        self,
        ctx: Context,
        get_ssh_conn_info_fn: Callable[..., SSHConnectionInfo],
        get_dhcpcd_configure_info_fn: Callable[..., DHCPCDConfigurationInfo],
        collaborators: CoreCollaborators,
        args: RemoteMachineNetworkConfigureArgs,
    ) -> tuple[SSHConnectionInfo, DHCPCDConfigurationInfo]:

        ssh_conn_info = get_ssh_conn_info_fn(ctx, collaborators, args.remote_opts)
        dhcpcd_configure_info = get_dhcpcd_configure_info_fn(ctx, collaborators, args, ssh_conn_info)

        tuple_info = (ssh_conn_info, dhcpcd_configure_info)
        network_info = self._bundle_network_information_from_tuple(ctx, tuple_info)

        collaborators.summary().show_summary_and_prompt_for_enter("Configure Network")

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
                ansible_vars=[
                    f"host_name={network_info.ssh_hostname}",
                    f"static_ip={dhcpcd_configure_info.static_ip_address}",
                    f"gateway_address={dhcpcd_configure_info.gw_ip_address}",
                    f"dns_address={dhcpcd_configure_info.dns_ip_address}",
                ],
                ansible_tags=["configure_rpi_network", "define_static_ip", "reboot"],
                selected_hosts=ssh_conn_info.host_ip_pairs,
            ),
            desc_run="Running Ansible playbook (Configure Network)",
            desc_end="Ansible playbook finished (Configure Network).",
        )
        collaborators.printer().new_line_fn()
        collaborators.printer().print_fn(output)

        return tuple_info

    def _print_post_run_instructions(
        self,
        ctx: Context,
        tuple_info: tuple[SSHConnectionInfo, DHCPCDConfigurationInfo],
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
            single_pair_item = ssh_conn_info.host_ip_pairs[0]
            return (single_pair_item.host, single_pair_item.ip_address)

    def _maybe_add_hosts_file_entry(
        self,
        ctx: Context,
        tuple_info: tuple[SSHConnectionInfo, DHCPCDConfigurationInfo],
        collaborators: CoreCollaborators,
    ):
        network_info = self._bundle_network_information_from_tuple(ctx, tuple_info)

        if collaborators.prompter().prompt_yes_no_fn(
            message=f"Add entry '{network_info.ssh_hostname} {network_info.static_ip_address}' to /etc/hosts file ({color.RED}password required{color.NONE})",
            post_no_message="Skipped adding new entry to /etc/hosts",
            post_yes_message=f"Selected to update /etc/hosts file",
        ):
            collaborators.hosts_file().add_entry_fn(
                ip_address=network_info.static_ip_address,
                dns_names=[network_info.ssh_hostname],
                comment="Added by provisioner",
            )

    def _print_pre_run_instructions(self, collaborators: CoreCollaborators):
        collaborators.printer().print_fn(generate_logo_network())
        collaborators.printer().print_with_rich_table_fn(generate_instructions_pre_network())
        collaborators.prompter().prompt_for_enter_fn()

    def _bundle_network_information_from_tuple(
        self, ctx: Context, tuple_info: tuple[SSHConnectionInfo, DHCPCDConfigurationInfo]
    ):
        ssh_conn_info = tuple_info[0]
        ssh_username = ssh_conn_info.username

        hostname_ip_tuple = self._extract_host_ip_tuple(ctx, ssh_conn_info)
        ssh_hostname = hostname_ip_tuple[0]
        ssh_ip_address = hostname_ip_tuple[1]

        dhcpcd_configure_info = tuple_info[1]
        static_ip_address = dhcpcd_configure_info.static_ip_address

        return RemoteMachineNetworkConfigureRunner.NetworkInfoBundle(
            ssh_username=ssh_username,
            ssh_hostname=ssh_hostname,
            ssh_ip_address=ssh_ip_address,
            static_ip_address=static_ip_address,
        )

    def _prerequisites(self, ctx: Context, checks: Checks) -> None:
        if ctx.os_arch.is_linux():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_darwin():
            checks.check_tool_fn("docker")

        elif ctx.os_arch.is_windows():
            raise NotImplementedError("Windows is not supported")
        else:
            raise NotImplementedError("OS is not supported")


def generate_logo_network() -> str:
    return f"""
 ██████╗ ███████╗    ███╗   ██╗███████╗████████╗██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗
██╔═══██╗██╔════╝    ████╗  ██║██╔════╝╚══██╔══╝██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝
██║   ██║███████╗    ██╔██╗ ██║█████╗     ██║   ██║ █╗ ██║██║   ██║██████╔╝█████╔╝
██║   ██║╚════██║    ██║╚██╗██║██╔══╝     ██║   ██║███╗██║██║   ██║██╔══██╗██╔═██╗
╚██████╔╝███████║    ██║ ╚████║███████╗   ██║   ╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗
 ╚═════╝ ╚══════╝    ╚═╝  ╚═══╝╚══════╝   ╚═╝    ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝"""


def generate_instructions_pre_network() -> str:
    return f"""
  Select a remote Raspberry Pi node ([yellow]ethernet connected[/yellow]) to set a static IP address.
  It uses DHCPCD (Dynamic Host Configuration Protocol Client Daemon a.k.a DHCP client daemon).

  It is vital for a RPi server to have a predictable address to interact with.
  Every time the Raspberry Pi node will connects to the network, it will use the same address.
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

  To declare the new static node in the provisioner config, add to ~/.config/provisioner/config.yaml:

    provisioner:
        remote:
            hosts:
              - name: <NAME>
                address: <IP-ADDRESS>
"""
