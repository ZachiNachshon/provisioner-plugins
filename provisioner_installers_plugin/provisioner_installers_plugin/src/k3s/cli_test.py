# !/usr/bin/env python3

import unittest

from provisioner.main import root_menu
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner


# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_installers_plugin/provisioner_installers_plugin/src/k3s/cli_test.py
#
class UtilityInstallerk3sTestShould(unittest.TestCase):

    def test_k8s_k3s_distro_prints_to_menu_as_expected(self) -> None:
        output = TestCliRunner.run(
            root_menu,
            [
                "install",
                "k8s",
                "distro",
            ],
        )
        self.assertIn("k3s-agent   Install a Rancher K3s Agent as a service", output)
        self.assertIn("k3s-server  Install a Rancher K3s Server as a service", output)
