#!/usr/bin/env python3

from loguru import logger
from python_core_lib.colors import color
from python_core_lib.infra.context import Context
from python_core_lib.infra.evaluator import Evaluator
from python_core_lib.shared.collaborators import CoreCollaborators
from python_core_lib.utils.checks import Checks
from python_core_lib.utils.hosts_file import HostsFile
from python_core_lib.utils.printer import Printer
from python_core_lib.utils.prompter import Prompter

from python_features_lib.remote.remote_connector import (
    RemoteMachineConnector,
    SSHConnectionInfo,
)
from python_features_lib.remote.typer_remote_opts import CliRemoteOpts

class RemoteMachineNetworkConfigureArgs:
    gw_ip_address: str
    dns_ip_address: str
    static_ip_address: str
    ansible_playbook_relative_path_from_root: str
    remote_opts: CliRemoteOpts

    def __init__(
        self,
        remote_opts: CliRemoteOpts,
        gw_ip_address: str,
        dns_ip_address: str,
        static_ip_address: str,
        ansible_playbook_relative_path_from_root: str,
    ) -> None:
        self.gw_ip_address = gw_ip_address
        self.dns_ip_address = dns_ip_address
        self.static_ip_address = static_ip_address
        self.ansible_playbook_relative_path_from_root = ansible_playbook_relative_path_from_root
        self.remote_opts = remote_opts

class RemoteMachineNetworkConfigureRunner:
    def run(self, ctx: Context, args: RemoteMachineNetworkConfigureArgs, collaborators: CoreCollaborators) -> None:
        logger.debug("Inside RemoteMachineNetworkConfigureRunner run()")

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

        dhcpcd_configure_info = Evaluator.eval_step_return_failure_throws(
            call=lambda: remote_connector.collect_dhcpcd_configuration_info(
                ctx, ssh_conn_info.host_ip_pairs, args.static_ip_address, args.gw_ip_address, args.dns_ip_address
            ),
            ctx=ctx,
            err_msg="Could not resolve SSH connection info",
        )
        collaborators.__summary.add_values("dhcpcd_configure_info", dhcpcd_configure_info)

        hostname_ip_tuple = self._extract_host_ip_tuple(ctx, ssh_conn_info)
        ssh_hostname = hostname_ip_tuple[0]
        ssh_ip_address = hostname_ip_tuple[1]

        ansible_vars = [
            f"host_name={ssh_hostname}",
            f"static_ip={dhcpcd_configure_info.static_ip_address}",
            f"gateway_address={dhcpcd_configure_info.gw_ip_address}",
            f"dns_address={dhcpcd_configure_info.dns_ip_address}",
        ]

        collaborators.__summary.show_summary_and_prompt_for_enter("Configure Network")

        output = collaborators.__printer.progress_indicator.status.long_running_process_fn(
            call=lambda: collaborators.__ansible_runner.run_fn(
                working_dir=collaborators.__io.get_path_from_exec_module_root_fn(),
                username=ssh_conn_info.username,
                password=ssh_conn_info.password,
                ssh_private_key_file_path=ssh_conn_info.ssh_private_key_file_path,
                playbook_path=args.ansible_playbook_relative_path_from_root,
                ansible_vars=ansible_vars,
                ansible_tags=["configure_rpi_network", "define_static_ip", "reboot"],
                selected_hosts=ssh_conn_info.host_ip_pairs,
            ),
            desc_run="Running Ansible playbook (Configure Network)",
            desc_end="Ansible playbook finished (Configure Network).",
        )

        collaborators.__printer.new_line_fn()
        collaborators.__printer.print_fn(output)
        collaborators.__printer.print_with_rich_table_fn(
            generate_instructions_post_network(
                username=ssh_conn_info.username,
                hostname=ssh_hostname,
                ip_address=ssh_ip_address,
                static_ip=dhcpcd_configure_info.static_ip_address,
            )
        )

        self._maybe_add_hosts_file_entry(
            collaborators.__prompter,
            collaborators.__hosts_file,
            ssh_hostname,
            dhcpcd_configure_info.static_ip_address,
        )

    def _extract_host_ip_tuple(self, ctx: Context, ssh_conn_info: SSHConnectionInfo) -> tuple[str, str]:
        if ctx.is_dry_run():
            return ("DRY_RUN_RESPONSE", "DRY_RUN_RESPONSE")
        else:
            # Promised to have only single item
            single_pair_item = ssh_conn_info.host_ip_pairs[0]
            return (single_pair_item.host, single_pair_item.ip_address)

    def _maybe_add_hosts_file_entry(self, prompter: Prompter, hosts_file: HostsFile, hostname: str, static_ip: str):
        if prompter.prompt_yes_no_fn(
            message=f"Add entry '{hostname} {static_ip}' to /etc/hosts file ({color.RED}password required{color.NONE})",
            post_no_message="Skipped adding new entry to /etc/hosts",
            post_yes_message=f"Selected to update /etc/hosts file",
        ):
            hosts_file.add_entry_fn(ip_address=static_ip, dns_names=[hostname], comment="Added by provisioner")

    def _print_pre_run_instructions(self, printer: Printer, prompter: Prompter):
        printer.print_fn(generate_logo_network())
        printer.print_with_rich_table_fn(generate_instructions_pre_network())
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

  To declare the new static node in the provisioner config, add to <ROOT>/config.properties:

    Master:
      • // TODO

    Worker (replace X with the node number):
      • // TODO
"""
