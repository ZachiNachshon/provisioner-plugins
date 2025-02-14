#!/usr/bin/env python3

from provisioner_installers_plugin.src.installer.domain.installable import Installable
from provisioner_installers_plugin.src.installer.domain.source import (
    ActiveInstallSource,
    InstallSource,
)
from provisioner_installers_plugin.src.utilities.utilities_versions import ToolingVersions

SupportedOS = ["linux", "darwin"]
SupportedArchitectures = ["x86_64", "arm", "amd64", "armv6l", "armv7l", "arm64", "aarch64"]

SupportedToolingsCli = {
    "anchor": Installable.Utility(
        display_name="anchor",
        description="Create Dynamic CLI's as your GitOps Marketplace",
        binary_name="anchor",
        version=ToolingVersions.anchor_ver,
        version_command="version",
        active_source=ActiveInstallSource.GitHub,
        source=InstallSource(
            github=InstallSource.GitHub(
                owner="ZachiNachshon",
                repo="anchor",
                supported_releases=["darwin_amd64", "darwin_arm64", "linux_amd64", "linux_arm", "linux_arm64"],
                release_name_resolver=lambda version, os, arch: f"anchor_{version.removeprefix('v')}_{os}_{arch}.tar.gz",
            ),
        ),
    ),
    "helm": Installable.Utility(
        display_name="helm",
        description="Package Manager for Kubernetes",
        binary_name="helm",
        version=ToolingVersions.helm_ver,
        # Need to extract the version from string
        # version.BuildInfo{Version:"v3.14.1", GitCommit:"e8858f8696b144ee7c533bd9d49a353ee6c4b98d", GitTreeState:"clean", GoVersion:"go1.21.7"}
        version_command="--version",
        active_source=ActiveInstallSource.GitHub,
        source=InstallSource(
            github=InstallSource.GitHub(
                owner="helm",
                repo="helm",
                supported_releases=["darwin_amd64", "darwin_arm64", "linux_amd64", "linux_arm", "linux_arm64"],
                release_name_resolver=lambda version, os, arch: f"helm-{version}-{os}-{arch}.tar.gz",
            ),
        ),
    ),
}
