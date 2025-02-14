#!/usr/bin/env python3

from provisioner_installers_plugin.src.installer.domain.installable import Installable
from provisioner_installers_plugin.src.installer.domain.source import (
    ActiveInstallSource,
    InstallSource,
)
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
                install_fn=lambda version, collaborators: install_python(version, collaborators),
            ),
        ),
    ),
}


# Move from here
def install_python(maybe_ver: str, collaborators: CoreCollaborators) -> str:
    # Install python  / pip uisng pyenv into managed folder i.e. ~/.local/bin
    print("=================================")
    print(f"Installing Python version {maybe_ver}")
    print("=================================")


#   f"apt-get install -y python{version} python{version}-distutils python{version}-dev",
