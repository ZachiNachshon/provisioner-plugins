#!/usr/bin/env python3

import unittest

import pytest

from provisioner.main import root_menu
from provisioner_shared.test_lib.rpi_os_container import RemoteRPiOsContainer
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner
from provisioner_shared.test_lib.test_env import TestEnv

ARG_GW_IP_ADDRESS = "1.1.1.1"
ARG_DNS_IP_ADDRESS = "192.168.1.1"
ARG_STATIC_IP_ADDRESS = "1.1.1.200"


# To run as a single test target:
#  ./run_tests.py plugins/provisioner_single_board_plugin/provisioner_single_board_plugin/src/raspberry_pi/node/network_cmd_e2e_test.py
#
@pytest.mark.e2e
class RaspberryPiNodeNetworkE2ETestShould(unittest.TestCase):
    env = TestEnv.create()

    @classmethod
    def setUpClass(cls):
        """Start the container once before any tests in this class."""
        cls.container = RemoteRPiOsContainer()
        try:
            cls.container.start()
        except Exception as e:
            print(f"Failed to start container: {str(e)}")
            raise

    @classmethod
    def tearDownClass(cls):
        """Stop the container after all tests in this class have completed."""
        if hasattr(cls, "container") and cls.container:
            try:
                cls.container.stop()
            except Exception as e:
                print(f"Error stopping container: {str(e)}")
            finally:
                cls.container = None

    def test_e2e_configure_network_settings_successfully(self):
        """Test full network configuration including hostname and WiFi settings."""
        output = TestCliRunner.run(
            root_menu,
            [
                "single-board",
                "raspberry-pi",
                "node",
                "--environment",
                "Remote",
                "--connect-mode",
                "Flags",
                "--node-username",
                "pi",
                "--node-password",
                "raspberry",
                "--ip-address",
                "127.0.0.1",
                "--port",
                str(self.container.ssh_port),
                "--hostname",
                "test-node",
                "--verbosity",
                "Verbose",
                "-vy",
                "network",
                "--static-ip-address",
                ARG_STATIC_IP_ADDRESS,
                "--gw-ip-address",
                ARG_GW_IP_ADDRESS,
                "--dns-ip-address",
                ARG_DNS_IP_ADDRESS,
                # TODO: add the following flags to the command
                # "--wifi-country",
                # "IL",
                # "--wifi-ssid",
                # "test-wifi",
                # "--wifi-password",
                # "test-password",
            ],
        )

        # Verify the configuration commands were executed
        self.assertIn("Mock raspi-config: do_hostname test-node", output)
        self.assertIn("Mock raspi-config: do_wifi_country IL", output)
        # self.assertIn("Mock raspi-config: do_wifi_ssid_passphrase test-wifi test-password", output)
