#!/usr/bin/env python3

from typing import Optional

from provisioner_installers_plugin.installer.domain.source import (
    ActiveInstallSource,
    InstallSources,
)

SupportedOS = ["linux", "darwin"]
SupportedArchitectures = ["x86_64", "arm", "amd64", "armv6l", "armv7l", "arm64", "aarch64"]


class Installable:
    class Utility:
        display_name: str
        binary_name: str
        version: str
        sources: InstallSources
        active_source: ActiveInstallSource

        def __init__(
            self,
            display_name: str,
            binary_name: str,
            version: Optional[str] = None,
            sources: InstallSources = None,
            active_source: ActiveInstallSource = None,
        ) -> None:

            self.display_name = display_name
            self.binary_name = binary_name
            self.version = version
            self.sources = sources
            self.active_source = active_source

        def has_install_script(self) -> bool:
            return self.script and len(self.script.install_cmd) > 0
