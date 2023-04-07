#!/usr/bin/env python3

from enum import Enum
from typing import Callable, List

from python_core_lib.utils.os import OsArch


class ActiveInstallSource(str, Enum):
    GitHub = "GitHub"
    Script = "Script"


class InstallSources:
    class Script:
        install_cmd: str

        def __init__(self, install_cmd: str):
            self.install_cmd = install_cmd

    class GitHub:
        owner: str
        repo: str
        supported_releases: dict[str, str]
        github_access_token: str
        release_name_resolver: Callable[[str, str, str], str]

        def __init__(
            self,
            owner: str,
            repo: str,
            supported_releases: List[str],
            github_access_token: str = None,
            release_name_resolver: Callable[[str, str, str], str] = None,
        ) -> None:

            self.owner = owner
            self.repo = repo
            self.supported_releases = supported_releases
            self.github_access_token = github_access_token
            self.release_name_resolver = release_name_resolver

        def _is_binary_supported_by_os_arch(self, os_arch: OsArch) -> bool:
            os_arch_pair = os_arch.as_pair(mapping={"x86_64": "amd64"})
            return self.supported_releases and os_arch_pair in self.supported_releases

        def resolve_binary_release_name(self, os_arch: OsArch, version: str) -> str:
            if not self._is_binary_supported_by_os_arch(os_arch):
                return None
            return self.release_name_resolver(version, os_arch.os, os_arch.arch)

    def __init__(self, github: "InstallSources.GitHub" = None, script: "InstallSources.Script" = None) -> None:
        self.github = github
        self.script = script

    github: "InstallSources.GitHub"
    script: "InstallSources.Script"
