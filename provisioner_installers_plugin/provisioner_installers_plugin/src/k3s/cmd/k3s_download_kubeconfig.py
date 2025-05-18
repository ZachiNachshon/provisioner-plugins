#!/usr/bin/env python3


from loguru import logger
from provisioner_installers_plugin.src.k3s.cmd.remote_k3s_download_kubeconfig import RemoteK3sKubeConfigDownloadArgs, RemoteK3sKubeConfigDownloadRunner

from provisioner_shared.components.remote.remote_opts import RemoteOpts
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators


class K3sKubeConfigDownloadCmdArgs:

    remote_opts: RemoteOpts

    def __init__(self, remote_opts: RemoteOpts = None, dest_file_path: str = None) -> None:
        self.remote_opts = remote_opts
        self.dest_file_path = dest_file_path

    def print(self) -> None:
        if self.remote_opts:
            self.remote_opts.print()
        if self.dest_file_path:
            logger.debug("K3sKubeConfigDownloadCmdArgs: \n" + f"  dest_file_path: {self.dest_file_path}\n")


class K3sKubeConfigDownloadCmd:
    def run(self, ctx: Context, args: K3sKubeConfigDownloadCmdArgs) -> None:
        logger.debug("Inside K3sKubeConfigDownloadCmd run()")
        args.print()

        RemoteK3sKubeConfigDownloadRunner().run(
            ctx=ctx,
            args=RemoteK3sKubeConfigDownloadArgs(
                remote_opts=args.remote_opts,
                dest_file_path=args.dest_file_path,
            ),
            collaborators=CoreCollaborators(ctx),
        )
