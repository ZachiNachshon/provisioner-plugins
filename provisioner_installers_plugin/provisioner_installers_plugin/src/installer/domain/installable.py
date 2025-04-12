#!/usr/bin/env python3

from typing import Optional

from provisioner_installers_plugin.src.installer.domain.dynamic_args import DynamicArgs
from provisioner_installers_plugin.src.installer.domain.source import (
    ActiveInstallSource,
    InstallSource,
)

SupportedOS = ["linux", "darwin"]
SupportedArchitectures = ["x86_64", "arm", "amd64", "armv6l", "armv7l", "arm64", "aarch64"]


class Installable:
    class Utility:

        def __init__(
            self,
            display_name: str,
            description: str,
            binary_name: str,
            version: Optional[str] = None,
            source: InstallSource = None,
            active_source: ActiveInstallSource = None,
            version_command: str = None,
            maybe_args: Optional[DynamicArgs] = None,
        ) -> None:

            self.display_name = display_name
            self.description = description
            self.binary_name = binary_name
            self.version = version
            self.source = source
            self.active_source = active_source
            self.version_command = version_command
            self.maybe_args = maybe_args

        def has_script_active_source(self) -> bool:
            if self.active_source != ActiveInstallSource.Script:
                return False
            return self.source and self.source.script and len(self.source.script.install_script) > 0

        def has_github_active_source(self) -> bool:
            if self.active_source != ActiveInstallSource.GitHub:
                return False
            return self.source and self.source.github

        def has_callback_active_source(self) -> bool:
            if self.active_source != ActiveInstallSource.Callback:
                return False
            return self.source and self.source.callback and self.source.callback.install_fn is not None

        def has_ansible_active_source(self) -> bool:
            if self.active_source != ActiveInstallSource.Ansible:
                return False
            return self.source and self.source.ansible and self.source.ansible.playbook is not None

        def as_summary_object(self, verbose: Optional[bool] = False) -> "Installable.Utility":
            return Installable.Utility(
                display_name=self.display_name,
                description=self.description,
                binary_name=self.binary_name,
                version=self.version,
                active_source=self.active_source,
                source=self.source.as_summary_object(verbose),
                version_command=self.version_command,
                maybe_args=self.maybe_args,
            )
