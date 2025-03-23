#!/usr/bin/env python3

import os
import unittest
from unittest import mock

from provisioner.main import root_menu
from provisioner_single_board_plugin.main_fake import get_fake_app

from provisioner_shared.components.runtime.errors.cli_errors import (
    CliApplicationException,
    StepEvaluationFailure,
)
from provisioner_shared.test_lib.assertions import Assertion
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner
from provisioner_shared.test_lib.test_env import TestEnv



RPI_NODE_MODULE_PATH = "provisioner_single_board_plugin.src.raspberry_pi.node"

STEP_ERROR_OUTPUT = "This is a sample step error output for a test expected to fail"


# To run as a single test target:
#  ./run_tests.py plugins/provisioner_single_board_plugin/provisioner_single_board_plugin/src/raspberry_pi/node/cli_test.py
#
class RaspberryPiNodeCliTestShould(unittest.TestCase):

    env = TestEnv.create()

    # @staticmethod
    # def create_network_configure_runner():
    #     return TestCliRunner.run(
    #         get_fake_app(),
    #         [
    #             "--dry-run",
    #             "--verbose",
    #             "--auto-prompt",
    #             "single-board",
    #             "raspberry-pi",
    #             "node",
    #             "network",
    
    #         ],
    #     )

    @mock.patch(f"{RPI_NODE_MODULE_PATH}.configure_cmd.RPiOsConfigureCmd.run", side_effect=Exception())
    def test_run_rpi_node_configure_cmd_unmanaged_failure(self, run_call: mock.MagicMock) -> None:
        Assertion.expect_raised_failure(
            self,
            ex_type=CliApplicationException,
            method_to_run=lambda: TestCliRunner.run_throws_not_managed(
                root_menu,
                [
                    "single-board",
                    "raspberry-pi",
                    "node",
                    "configure",
                    "--verbose",
                    "--auto-prompt",
                ]
            )
        )
    
    @mock.patch(
        f"{RPI_NODE_MODULE_PATH}.configure_cmd.RPiOsConfigureCmd.run",
        side_effect=StepEvaluationFailure(STEP_ERROR_OUTPUT),
    )
    def test_run_rpi_node_configure_cmd_managed_failure(self, run_call: mock.MagicMock) -> None:
        Assertion.expect_output(
            self,
            expected=STEP_ERROR_OUTPUT,
            method_to_run=lambda: TestCliRunner.run(
                root_menu,
                [
                    "single-board",
                    "raspberry-pi",
                    "node",
                    "configure",
                    "--verbose",
                    "--auto-prompt",
                ]
            )
        )

    @mock.patch(
        f"{RPI_NODE_MODULE_PATH}.network_cmd.RPiNetworkConfigureCmd.run",
        side_effect=StepEvaluationFailure(STEP_ERROR_OUTPUT),
    )
    def test_run_rpi_node_network_cmd_managed_failure(self, run_call: mock.MagicMock) -> None:
        Assertion.expect_output(
            self,
            expected=STEP_ERROR_OUTPUT,
            method_to_run=lambda: TestCliRunner.run(
                root_menu,
                [
                    "single-board",
                    "raspberry-pi",
                    "node",
                    "network",
                    "--verbose",
                    "--auto-prompt",
                ]
            )
        )

    @mock.patch(f"{RPI_NODE_MODULE_PATH}.network_cmd.RPiNetworkConfigureCmd.run", side_effect=Exception())
    def test_run_rpi_node_network_cmd_unmanaged_failure(self, run_call: mock.MagicMock) -> None:
        Assertion.expect_raised_failure(
            self,
            ex_type=CliApplicationException,
            method_to_run=lambda: TestCliRunner.run_throws_not_managed(
                root_menu,
                [
                    "single-board",
                    "raspberry-pi",
                    "node",
                    "network",
                    "--verbose",
                    "--auto-prompt",
                ]
            )
        )
