#!/usr/bin/env python3

from provisioner_installers_plugin.src.installer.domain.installable import Installable
from provisioner_installers_plugin.src.installer.domain.source import (
    ActiveInstallSource,
    InstallSource,
)
from provisioner_installers_plugin.src.utilities.utilities_versions import ToolingVersions

from provisioner_shared.components.runtime.runner.ansible.ansible_runner import AnsiblePlaybook

SupportedOS = ["linux", "darwin"]
SupportedArchitectures = ["x86_64", "arm", "amd64", "armv6l", "armv7l", "arm64", "aarch64"]

SupportedToolingsK8s = {
    "k3s-server": Installable.Utility(
        display_name="k3s-server",
        description="Fully compliant lightweight Kubernetes distribution (https://k3s.io)",
        binary_name="k3s",
        version=ToolingVersions.k3s_server_ver,
        version_command="k3s --version",
        active_source=ActiveInstallSource.Ansible,
        source=InstallSource(
            ansible=InstallSource.Ansible(
                playbook=AnsiblePlaybook(
                    name="k3s_server_install",
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
                ansible_vars=["server_install=True"],
            ),
        ),
    ),
    "k3s-agent": Installable.Utility(
        display_name="k3s-agent",
        description="Fully compliant lightweight Kubernetes distribution (https://k3s.io)",
        binary_name="k3s",
        version=ToolingVersions.k3s_agent_ver,
        active_source=ActiveInstallSource.Ansible,
        source=InstallSource(
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
                ansible_vars=["agent_install=True"],
            ),
        ),
    ),
}
