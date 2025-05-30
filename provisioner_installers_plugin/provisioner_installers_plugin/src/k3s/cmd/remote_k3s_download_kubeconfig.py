#!/usr/bin/env python3

import os
import subprocess
from typing import Optional

from loguru import logger

from provisioner_shared.components.remote.remote_connector import (
    RemoteMachineConnector,
    SSHConnectionInfo,
)
from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.infra.evaluator import Evaluator
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.runtime.utils.checks import Checks

K3S_KUBECONFIG_DEFAULT_SERVER_URL = "https://127.0.0.1:6443"


class RemoteK3sKubeConfigDownloadArgs:
    def __init__(
        self, remote_opts: RemoteOpts, dest_file_path: Optional[str] = None, server_url: Optional[str] = None
    ) -> None:
        self.remote_opts = remote_opts
        self.server_url = server_url
        if dest_file_path:
            self.dest_file_path = os.path.expanduser(dest_file_path)
        else:
            self.dest_file_path = os.path.expanduser("~/.kube/k3s/config")


class RemoteK3sKubeConfigDownloadRunner:
    def run(self, ctx: Context, args: RemoteK3sKubeConfigDownloadArgs, collaborators: CoreCollaborators) -> None:
        logger.debug("Inside RemoteK3sKubeConfigDownloadRunner run()")

        self._prerequisites(ctx=ctx, checks=collaborators.checks())
        ssh_conn_info = self._get_ssh_conn_info(ctx, collaborators, args.remote_opts)
        self._download_kubeconfig_with_progress_bar(
            ctx=ctx,
            ssh_conn_info=ssh_conn_info,
            collaborators=collaborators,
            args=args,
        )

    def _download_kubeconfig_with_progress_bar(
        self,
        ctx: Context,
        ssh_conn_info: SSHConnectionInfo,
        collaborators: CoreCollaborators,
        args: RemoteK3sKubeConfigDownloadArgs,
    ) -> None:
        ansible_host = ssh_conn_info.ansible_hosts[0]
        remote_ip = ansible_host.ip_address
        remote_user = ansible_host.username

        collaborators.summary().show_summary_and_prompt_for_enter(
            "Downloading K3s Kubeconfig, SSH password may be required"
        )

        self._download_kubeconfig(
            ctx,
            collaborators,
            remote_user,
            remote_ip,
            args.dest_file_path,
        )

        if args.server_url:
            self._update_kubeconfig_server_url(collaborators, args.dest_file_path, args.server_url)

    def _update_kubeconfig_server_url(
        self, collaborators: CoreCollaborators, kubeconfig_path: str, server_url: str
    ) -> None:
        kubeconfig_content: str = collaborators.io_utils().read_file_safe_fn(kubeconfig_path)
        kubeconfig_content = kubeconfig_content.replace(K3S_KUBECONFIG_DEFAULT_SERVER_URL, server_url)
        collaborators.io_utils().write_file_fn(kubeconfig_content, kubeconfig_path)

    def _download_kubeconfig(
        self,
        ctx: Context,
        collaborators: CoreCollaborators,
        remote_user: str,
        remote_ip: str,
        dest_file_path: str,
    ) -> str:
        # Create the directory structure
        collaborators.io_utils().create_directory_fn(os.path.dirname(dest_file_path))
        # Create empty file with proper permissions
        # Path(dest_file_path).touch(exist_ok=True)
        # os.chmod(dest_file_path, 0o600)

        if ctx.is_dry_run():
            return f"[DRY-RUN] Would download kubeconfig from {remote_user}@{remote_ip} to {dest_file_path}"

        try:
            # Download the kubeconfig from remote server
            ssh_cmd = f'ssh -o ConnectTimeout=5 {remote_user}@{remote_ip} "sudo cat /etc/rancher/k3s/k3s.yaml" > {dest_file_path}'
            collaborators.process().run_fn(args=[ssh_cmd], fail_on_error=True, allow_single_shell_command_str=True)
            return f"Successfully downloaded kubeconfig from {remote_user}@{remote_ip} to {dest_file_path}"
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to download kubeconfig: {str(e)}"
            collaborators.printer().print_fn(error_msg)
            raise RuntimeError(error_msg)

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
