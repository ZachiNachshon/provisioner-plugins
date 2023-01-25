#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_features_lib.anchor.typer_anchor_opts_fakes import TestDataAnchorOpts
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv
from typer.testing import CliRunner

from provisioner_single_board_plugin.main_fake import get_fake_app

runner = CliRunner()

ARG_GW_IP_ADDRESS = "1.1.1.1"
ARG_DNS_IP_ADDRESS = "2.2.2.2"
ARG_STATIC_IP_ADDRESS = "1.1.1.200"

RPI_NODE_NETWORK_CONFIGURE_RUNNER_PATH = (
    "provisioner_single_board_plugin.raspberry_pi.node.network_cmd.RPiNetworkConfigureCmd"
)

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_single_board_plugin/raspberry_pi/node/cli_test.py
#
class RaspberryPiNodeCliTestShould(unittest.TestCase):

    env = TestEnv.create()

    # @mock.patch("provisioner_single_board_plugin.raspberry_pi.node.configure_cmd.RPiNetworkConfigureCmd.run")
    # def test_rpi_node_run_configure_cli_cmd_with_args_success(self, run_call: mock.MagicMock) -> None:

    #     runner.invoke(
    #         get_fake_app(),
    #         ["--dry-run", "--verbose", "provisioner", "single-board", "raspberry-pi", "configure"],
    #     )

    #     Assertion.expect_call_argument(self, run_call, arg_name="ctx", expected_value=self.env.get_context())

    @mock.patch(f"{RPI_NODE_NETWORK_CONFIGURE_RUNNER_PATH}.run")
    def test_rpi_node_run_network_cli_cmd_with_args_success(self, run_call: mock.MagicMock) -> None:

        runner.invoke(
            get_fake_app(),
            [
                "--dry-run",
                "--verbose",
                "provisioner",
                "single-board",
                "raspberry-pi",
                "node",
                "network",
                f"--static-ip-address={ARG_STATIC_IP_ADDRESS}",
                f"--gw-ip-address={ARG_GW_IP_ADDRESS}",
                f"--dns-ip-address={ARG_DNS_IP_ADDRESS}",
            ],
        )
        self.assertEqual(1, run_call.call_count)

        def assertion_callback(args):
            self.assertEqual(args.static_ip_address, ARG_STATIC_IP_ADDRESS)
            self.assertEqual(args.gw_ip_address, ARG_GW_IP_ADDRESS)
            self.assertEqual(args.dns_ip_address, ARG_DNS_IP_ADDRESS)

        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
        Assertion.expect_call_argument(self, run_call, arg_name="ctx", expected_value=self.env.get_context())

    # RPI_NODE_CLI_ARG_ANCHOR_RUN_CMD = "run --action=test-action"

    # @mock.patch("provisioner_single_board_plugin.raspberry_pi.node.cli.RPiNetworkConfigureCmd.run")
    # def test_rpi_node_cli_with_args_success(self, run_call: mock.MagicMock) -> None:

    #     runner.invoke(
    #         get_fake_app(),
    #         ["--dry-run", "--verbose", "examples", "anchor", "run-command",
    #         f"--anchor-run-command={RPI_NODE_CLI_ARG_ANCHOR_RUN_CMD}",
    #         f"--github-organization={TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_ORGANIZATION}",
    #         f"--repository-name={TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_REPOSITORY}",
    #         f"--branch-name={TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_BRANCH}",
    #         f"--github-access-token={TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_GITHUB_ACCESS_TOKEN}",
    #         ],
    #     )

    #     def assertion_callback(args):
    #         self.assertEqual(args.anchor_run_command, RPI_NODE_CLI_ARG_ANCHOR_RUN_CMD)
    #         self.assertEqual(args.github_organization, TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_ORGANIZATION)
    #         self.assertEqual(args.repository_name, TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_REPOSITORY)
    #         self.assertEqual(args.branch_name, TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_BRANCH)
    #         self.assertEqual(args.github_access_token, TestDataAnchorOpts.TEST_DATA_ANCHOR_GITHUB_GITHUB_ACCESS_TOKEN)

    #     Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
    #     Assertion.expect_call_argument(self, run_call, arg_name="ctx", expected_value=self.env.get_context())
