#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_single_board_plugin.src.raspberry_pi.node.network_cmd import (
    RPiNetworkConfigureCmd,
    RPiNetworkConfigureCmdArgs,
)

from provisioner_shared.components.remote.typer_remote_opts_fakes import TestDataRemoteOpts
from provisioner_shared.components.runtime.test_lib.assertions import Assertion
from provisioner_shared.components.runtime.test_lib.test_env import TestEnv

ARG_GW_IP_ADDRESS = "1.1.1.1"
ARG_DNS_IP_ADDRESS = "2.2.2.2"
ARG_STATIC_IP_ADDRESS = "1.1.1.200"

RPI_REMOTE_NETWORK_CONFIGURE_RUNNER_PATH = (
    "provisioner_single_board_plugin.src.common.remote.remote_network_configure.RemoteMachineNetworkConfigureRunner"
)


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_single_board_plugin/raspberry_pi/node/configure_cmd_test.py
#
class RPiNetworkConfigureCmdTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_network_configure_args(self) -> RPiNetworkConfigureCmdArgs:
        return RPiNetworkConfigureCmdArgs(
            gw_ip_address=ARG_GW_IP_ADDRESS,
            dns_ip_address=ARG_DNS_IP_ADDRESS,
            static_ip_address=ARG_STATIC_IP_ADDRESS,
            remote_opts=TestDataRemoteOpts.create_fake_cli_remote_opts(),
        )

    @mock.patch(f"{RPI_REMOTE_NETWORK_CONFIGURE_RUNNER_PATH}.run")
    def test_configure_network_cmd_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        fake_cmd_args = self.create_fake_network_configure_args()

        RPiNetworkConfigureCmd().run(ctx=self.env.get_context(), args=fake_cmd_args)

        def assertion_callback(args):
            self.assertEqual(args.gw_ip_address, fake_cmd_args.gw_ip_address)
            self.assertEqual(args.dns_ip_address, fake_cmd_args.dns_ip_address)
            self.assertEqual(args.static_ip_address, fake_cmd_args.static_ip_address)

        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
        Assertion.expect_call_argument(self, run_call, arg_name="ctx", expected_value=self.env.get_context())
