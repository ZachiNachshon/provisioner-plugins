# !/usr/bin/env python3

import re
import unittest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner


# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_installers_plugin/provisioner_installers_plugin/src/k3s/cli_test.py
#
class UtilityInstallerk3sTestShould(unittest.TestCase):

    def test_k8s_k3s_distro_prints_to_menu_as_expected(self) -> None:
        result = TestCliRunner.run_throws_not_managed(
            root_menu,
            [
                "install",
                "k8s",
                "distro",
            ],
        )
        
        # Use regex to match command descriptions with flexible spacing
        k3s_agent_pattern = re.compile(r'k3s-agent\s+Install or uninstall a Rancher K3s Agent')
        k3s_info_pattern = re.compile(r'k3s-info\s+Gather and display K3s configuration')
        k3s_kubeconfig_pattern = re.compile(r'k3s-kubeconfig\s+Download K3s kubeconfig from a remote server')
        k3s_server_pattern = re.compile(r'k3s-server\s+Install or uninstall a Rancher K3s Server')
        
        self.assertIsNotNone(k3s_agent_pattern.search(result.output))
        self.assertIsNotNone(k3s_info_pattern.search(result.output))
        self.assertIsNotNone(k3s_kubeconfig_pattern.search(result.output))
        self.assertIsNotNone(k3s_server_pattern.search(result.output))
