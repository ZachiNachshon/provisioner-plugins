#!/usr/bin/env python3

from provisioner_installers_plugin.src.installer.domain.installable import Installable
from provisioner_installers_plugin.src.installer.domain.source import (
    ActiveInstallSource,
    InstallSource,
)
from provisioner_installers_plugin.src.installer.domain.dynamic_args import DynamicArgs
from provisioner_installers_plugin.src.utilities.utilities_versions import ToolingVersions

from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators

SupportedOS = ["linux", "darwin"]
SupportedArchitectures = ["x86_64", "arm", "amd64", "armv6l", "armv7l", "arm64", "aarch64"]

SupportedToolingsSystem = {
    "python": Installable.Utility(
        display_name="python",
        description="Python / pip package manager",
        binary_name="python",
        version=ToolingVersions.helm_ver,
        version_command="-V",
        active_source=ActiveInstallSource.Callback,
        source=InstallSource(
            callback=InstallSource.Callback(
                install_fn=lambda version, collaborators, maybe_args: install_python(version, collaborators, maybe_args),
                uninstall_fn=lambda version, collaborators, maybe_args: uninstall_python(version, collaborators, maybe_args),
            ),
        ),
    ),
}


# Move from here
def install_python(maybe_ver: str, collaborators: CoreCollaborators, maybe_args: DynamicArgs = None) -> str:
    # Install python  / pip uisng pyenv into managed folder i.e. ~/.local/bin
    print("=================================")
    print(f"Installing Python version {maybe_ver}")
    print("=================================")
    return "Python installed"

def uninstall_python(maybe_ver: str, collaborators: CoreCollaborators, maybe_args: DynamicArgs = None) -> str:
    # Uninstall python by removing symlinks (basic uninstall, actual Python is not removed)
    print("=================================")
    print(f"Uninstalling Python version {maybe_ver}")
    print("=================================")
    return "Python uninstalled"

#   f"apt-get install -y python{version} python{version}-distutils python{version}-dev",
