#!/usr/bin/env python3

from provisioner_installers_plugin.src.installer.domain.installable import Installable
from provisioner_installers_plugin.src.installer.domain.source import (
    ActiveInstallSource,
    InstallSource,
)
from provisioner_installers_plugin.src.k3s.installer import (
    install_k3s_agent,
    install_k3s_server,
    uninstall_k3s_agent,
    uninstall_k3s_server,
)
from provisioner_installers_plugin.src.utilities.utilities_versions import ToolingVersions

SupportedOS = ["linux", "darwin"]
SupportedArchitectures = ["x86_64", "arm", "amd64", "armv6l", "armv7l", "arm64", "aarch64"]

SupportedToolingsK8s = {
    "k3s-server": Installable.Utility(
        display_name="k3s-server",
        description="Fully compliant lightweight Kubernetes distribution (https://k3s.io)",
        binary_name="k3s",
        version=ToolingVersions.k3s_server_ver,
        version_command="--version",
        active_source=ActiveInstallSource.Callback,
        source=InstallSource(
            callback=InstallSource.Callback(
                install_fn=lambda version, collaborators, maybe_args: install_k3s_server(
                    version, collaborators, maybe_args
                ),
                uninstall_fn=lambda version, collaborators, maybe_args: uninstall_k3s_server(
                    version, collaborators, maybe_args
                ),
            ),
        ),
    ),
    "k3s-agent": Installable.Utility(
        display_name="k3s-agent",
        description="Fully compliant lightweight Kubernetes distribution (https://k3s.io)",
        binary_name="k3s",
        version=ToolingVersions.k3s_agent_ver,
        version_command="--version",
        active_source=ActiveInstallSource.Callback,
        source=InstallSource(
            callback=InstallSource.Callback(
                install_fn=lambda version, collaborators, maybe_args: install_k3s_agent(
                    version, collaborators, maybe_args
                ),
                uninstall_fn=lambda version, collaborators, maybe_args: uninstall_k3s_agent(
                    version, collaborators, maybe_args
                ),
            ),
        ),
    ),
}
