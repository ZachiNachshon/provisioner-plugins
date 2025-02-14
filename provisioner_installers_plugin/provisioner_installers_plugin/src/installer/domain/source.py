#!/usr/bin/env python3

from enum import Enum
from typing import Callable, List, Optional

from provisioner_shared.components.runtime.runner.ansible.ansible_runner import AnsiblePlaybook
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators
from provisioner_shared.components.runtime.utils.os import OsArch


class ActiveInstallSource(str, Enum):
    GitHub = "GitHub"
    Script = "Script"
    Ansible = "Ansible"
    Callback = "Callback"


class InstallSource:
    class Callback:
        # Callback(version, collaborators)
        def __init__(self, install_fn: Callable[[str, CoreCollaborators], str]):
            self.install_fn = install_fn

        def as_summary_object(self, verbose: Optional[bool] = False) -> "InstallSource.Callback":
            return self if verbose else None

    class Script:
        def __init__(self, install_script: str):
            self.install_script = install_script

        def as_summary_object(self, verbose: Optional[bool] = False) -> "InstallSource.Script":
            return self if verbose else None

    class Ansible:
        def __init__(
            self,
            playbook: AnsiblePlaybook,
            ansible_tags: Optional[List[str]] = [],
            ansible_vars: Optional[List[str]] = [],
        ):

            self.playbook = playbook
            self.ansible_tags = ansible_tags
            self.ansible_vars = ansible_vars

        def as_summary_object(self, verbose: Optional[bool] = False) -> "InstallSource.Ansible":
            return self if verbose else None

    class GitHub:
        def __init__(
            self,
            owner: str,
            repo: str,
            supported_releases: List[str],
            git_access_token: str = None,
            release_name_resolver: Callable[[str, str, str], str] = None,
        ) -> None:

            self.owner = owner
            self.repo = repo
            self.supported_releases = supported_releases
            self.git_access_token = git_access_token
            self.release_name_resolver = release_name_resolver

        def as_summary_object(self, verbose: Optional[bool] = False) -> "InstallSource.GitHub":
            return (
                InstallSource.GitHub(owner=self.owner, repo=self.repo, supported_releases=self.supported_releases)
                if verbose
                else None
            )

        def _is_binary_supported_by_os_arch(self, os_arch: OsArch) -> bool:
            os_arch_pair = os_arch.as_pair(mapping={"x86_64": "amd64"})
            return self.supported_releases and os_arch_pair in self.supported_releases

        def resolve_binary_release_name(self, os_arch: OsArch, version: str) -> str:
            if not self._is_binary_supported_by_os_arch(os_arch):
                return None
            return self.release_name_resolver(version, os_arch.os, os_arch.arch)

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
