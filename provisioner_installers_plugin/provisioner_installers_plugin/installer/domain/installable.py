#!/usr/bin/env python3

from typing import Optional

from provisioner_installers_plugin.installer.domain.source import (
    ActiveInstallSource,
    InstallSource,
)

SupportedOS = ["linux", "darwin"]
SupportedArchitectures = ["x86_64", "arm", "amd64", "armv6l", "armv7l", "arm64", "aarch64"]


class Installable:
    class Utility:
        display_name: str
        binary_name: str
        version: str
        source: InstallSource
        active_source: ActiveInstallSource

        def __init__(
            self,
            display_name: str,
            binary_name: str,
            version: Optional[str] = None,
            sources: InstallSource = None,
            active_source: ActiveInstallSource = None,
        ) -> None:

            self.display_name = display_name
            self.binary_name = binary_name
            self.version = version
            self.source = sources
            self.active_source = active_source

        def has_script_active_source(self) -> bool:
            if self.active_source != ActiveInstallSource.Script:
                return False
            return self.source and self.source.script and len(self.source.script.install_cmd) > 0

        def has_github_active_source(self) -> bool:
            if self.active_source != ActiveInstallSource.GitHub:
                return False
            return self.source and self.source.github

        def as_summary_object(self, verbose: Optional[bool] = False) -> "Installable.Utility":
            return Installable.Utility(
                display_name=self.display_name, 
                binary_name=self.binary_name, 
                version=self.version, 
                active_source=self.active_source, 
                sources=self.source.as_summary_object(verbose)
            ) 