#!/usr/bin/env python3

from python_core_lib.runner.ansible.ansible_runner import AnsiblePlaybook

from provisioner_installers_plugin.installer.domain.installable import Installable
from provisioner_installers_plugin.installer.domain.source import (
    ActiveInstallSource,
    InstallSource,
)
from provisioner_installers_plugin.installer.versions import ToolingVersions

SupportedOS = ["linux", "darwin"]
SupportedArchitectures = ["x86_64", "arm", "amd64", "armv6l", "armv7l", "arm64", "aarch64"]

SupportedToolings = {
    "anchor": Installable.Utility(
        display_name="anchor",
        binary_name="anchor",
        version=ToolingVersions.anchor_ver,
        active_source=ActiveInstallSource.GitHub,
        sources=InstallSource(
            github=InstallSource.GitHub(
                owner="ZachiNachshon",
                repo="anchor",
                supported_releases=["darwin_amd64", "darwin_arm64", "linux_amd64", "linux_arm", "linux_arm64"],
                release_name_resolver=lambda version, os, arch: f"anchor_{version.removeprefix('v')}_{os}_{arch}.tar.gz",
            ),
        ),
    ),
    "k3s-server": Installable.Utility(
        display_name="k3s-server",
        binary_name="k3s",
        version=ToolingVersions.k3s_server_ver,
        active_source=ActiveInstallSource.Ansible,
        sources=InstallSource(
            ansible=InstallSource.Ansible(
                playbook=AnsiblePlaybook(
                    name="k3s_master_install",
                    content="""
---
- name: Install K3s master server
  hosts: selected_hosts
  gather_facts: no
  {modifiers}

  roles:
    - role: {ansible_playbooks_path}/roles/k3s
""",
                ),
                ansible_vars=["master_install=True", f"k3s_version={ToolingVersions.k3s_server_ver}"],
            ),
        ),
    ),
    "k3s-agent": Installable.Utility(
        display_name="k3s-agent",
        binary_name="k3s",
        version=ToolingVersions.k3s_agent_ver,
        active_source=ActiveInstallSource.Ansible,
        sources=InstallSource(
            ansible=InstallSource.Ansible(
                playbook=AnsiblePlaybook(
                    name="k3s_agent_install",
                    content="""
---
- name: Install K3s agent and connect to remote master server
  hosts: selected_hosts
  gather_facts: no
  {modifiers}

  roles:
    - role: {ansible_playbooks_path}/roles/k3s
""",
                ),
                ansible_vars=["master_install=True", f"k3s_version={ToolingVersions.k3s_agent_ver}"],
            ),
        ),
    ),
    "helm": Installable.Utility(
        display_name="helm",
        binary_name="helm",
        version=ToolingVersions.helm_ver,
        active_source=ActiveInstallSource.GitHub,
        sources=InstallSource(
            github=InstallSource.GitHub(
                owner="helm",
                repo="helm",
                supported_releases=["darwin_amd64", "darwin_arm64", "linux_amd64", "linux_arm", "linux_arm64"],
                release_name_resolver=lambda version, os, arch: f"helm-{version}-{os}-{arch}.tar.gz",
            ),
        ),
    ),
}
