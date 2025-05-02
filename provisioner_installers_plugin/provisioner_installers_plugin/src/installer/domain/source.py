#!/usr/bin/env python3

from enum import Enum
from typing import Callable, Dict, List, Optional

from provisioner_installers_plugin.src.installer.domain.dynamic_args import DynamicArgs

from provisioner_shared.components.runtime.runner.ansible.ansible_runner import AnsiblePlaybook
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.runtime.utils.os import OsArch


class ActiveInstallSource(str, Enum):
    GitHub = "GitHub"
    Script = "Script"
    Ansible = "Ansible"
    Callback = "Callback"

    def __str__(self):
        return self.value


class InstallSource:
    class Callback:
        def __init__(
            self,
            install_fn: Callable[[str, CoreCollaborators, DynamicArgs], str],
            uninstall_fn: Callable[[str, CoreCollaborators, DynamicArgs], str],
        ):
            self.install_fn = install_fn
            self.uninstall_fn = uninstall_fn

        def as_summary_object(self, verbose: Optional[bool] = False) -> "InstallSource.Callback":
            return self if verbose else None

    class Script:
        def __init__(self, install_script: str, uninstall_script: Optional[str] = None):
            self.install_script = install_script
            self.uninstall_script = uninstall_script

        def as_summary_object(self, verbose: Optional[bool] = False) -> "InstallSource.Script":
            return self if verbose else None

    class Ansible:
        def __init__(
            self,
            playbook: AnsiblePlaybook,
            ansible_tags: Optional[List[str]] = [],
            ansible_vars: Optional[List[str]] = [],
            uninstall_tags: Optional[List[str]] = [],
        ):

            self.playbook = playbook
            self.ansible_tags = ansible_tags
            self.ansible_vars = ansible_vars
            self.uninstall_tags = uninstall_tags

        def as_summary_object(self, verbose: Optional[bool] = False) -> "InstallSource.Ansible":
            return self if verbose else None

    class GitHub:
        def __init__(
            self,
            owner: str,
            repo: str,
            supported_releases: List[str],
            git_access_token: str = None,
            arch_map: Dict[str, str] = {},
            release_name_resolver: Callable[[str, str, str], str] = None,
            alternative_base_url: str = None,
            archive_nested_binary_path: Optional[Callable[..., str]] = None,
        ) -> None:

            self.owner = owner
            self.repo = repo
            self.supported_releases = supported_releases
            self.git_access_token = git_access_token
            self.release_name_resolver = release_name_resolver
            self.arch_map = arch_map
            self.alternative_base_url = alternative_base_url
            self.archive_nested_binary_path = archive_nested_binary_path

        def as_summary_object(self, verbose: Optional[bool] = False) -> "InstallSource.GitHub":
            return (
                InstallSource.GitHub(owner=self.owner, repo=self.repo, supported_releases=self.supported_releases)
                if verbose
                else None
            )

        def _is_binary_supported_by_os_arch(self, os_arch_pair: OsArch) -> bool:
            return self.supported_releases and os_arch_pair in self.supported_releases

        def get_adjusted_os_arch(self, os_arch: OsArch) -> Optional[OsArch]:
            os_arch_pair = os_arch.as_pair(mapping=self.arch_map)
            if not self._is_binary_supported_by_os_arch(os_arch_pair):
                return None
            return OsArch.from_string(os_arch_pair)

        def resolve_binary_release_name(self, os_arch: OsArch, version: str) -> Optional[str]:
            adjusted_os_arch = self.get_adjusted_os_arch(os_arch)
            if not adjusted_os_arch:
                return None
            return self.release_name_resolver(version, adjusted_os_arch.os, adjusted_os_arch.arch)

    def as_summary_object(self, verbose: Optional[bool] = False) -> "InstallSource":
        if not verbose:
            return None
        result = InstallSource()
        if self.github:
            result.github = self.github.as_summary_object(verbose)
        if self.script:
            result.script = self.script.as_summary_object(verbose)
        if self.ansible:
            result.ansible = self.ansible.as_summary_object(verbose)
        if self.callback:
            result.callback = self.callback.as_summary_object(verbose)
        return result

    def __init__(
        self,
        github: "InstallSource.GitHub" = None,
        script: "InstallSource.Script" = None,
        ansible: "InstallSource.Ansible" = None,
        callback: "InstallSource.Callback" = None,
    ) -> None:

        self.github = github
        self.script = script
        self.ansible = ansible
        self.callback = callback
