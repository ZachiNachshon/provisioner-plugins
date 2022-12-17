#!/usr/bin/env python3

from typing import Optional

from python_core_lib.utils.os import OsArch

SupportedOS = ["linux", "darwin"]
SupportedArchitectures = ["x86_64", "arm", "amd64", "armv6l", "armv7l", "arm64", "aarch64"]

class Installables:

    class InstallableUtility:
        display_name: str
        name: str
        owner: str
        repo: str
        version: str
        install_cmd: str
        supported_binaries: dict[str, str]

        def __init__(self, 
            display_name: str, 
            name: str, 
            owner: str, 
            repo: str, 
            version: Optional[str] = None, 
            install_cmd: Optional[str] = None,
            supported_binaries: Optional[dict[str, str]] = None) -> None:

            self.display_name = display_name
            self.name = name
            self.owner = owner
            self.repo = repo
            self.version = version
            self.install_cmd = install_cmd
            self.supported_binaries = supported_binaries

        def has_install_command(self) -> bool:
            return self.install_cmd and len(self.install_cmd) > 0

        def generate_binary_url(self) -> str:
            return f"https://github.com/{self.owner}/{self.repo}/releases/latest"

        def get_binary_name_by_os_arch(self, os_arch: OsArch) -> str:
            if not self.supported_binaries:
                return None
            
            os_arch_pair = os_arch.as_pair(mapping={"x86_64": "amd64"})
            if os_arch_pair in self.supported_binaries:
                return self.supported_binaries[os_arch_pair]

            return None
        
    utilities: dict[str, InstallableUtility] = {}

    def __init__(self) -> None:
        self.populate_utilities()

    def populate_utilities(self) -> None:
        self.utilities["k3s-server"] = Installables.InstallableUtility(
            display_name="k3s-server",
            name="k3s",
            owner="k3s-io",
            repo="k3s",
            install_cmd="curl -sfL https://get.k3s.io | sh - ",
            supported_binaries = {
                "darwin_amd64s": "k3s",
                "darwin_arm64": "k3s",
            }
        )

        self.utilities["k3s-agent"] = Installables.InstallableUtility(
            display_name="k3s-agent",
            name="k3s",
            owner="k3s-io",
            repo="k3s",
            install_cmd="curl -sfL https://get.k3s.io | sh - "
        )

SupportedInstallables: Installables = Installables()