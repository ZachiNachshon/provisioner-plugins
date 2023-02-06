#!/usr/bin/env python3

import os
import unittest
from unittest import mock

from python_core_lib.errors.cli_errors import (
    CliApplicationException,
    StepEvaluationFailure,
)
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_cli_runner import TestCliRunner
from python_core_lib.test_lib.test_env import TestEnv
from typer.testing import CliRunner

from provisioner_single_board_plugin.main_fake import get_fake_app

ARG_GW_IP_ADDRESS = "1.1.1.1"
ARG_DNS_IP_ADDRESS = "2.2.2.2"
ARG_STATIC_IP_ADDRESS = "1.1.1.200"

RPI_NODE_MODULE_PATH = "provisioner_single_board_plugin.raspberry_pi.node"

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_single_board_plugin/raspberry_pi/node/cli_test.py
#
class RaspberryPiNodeCliTestShould(unittest.TestCase):

    env = TestEnv.create()

    @staticmethod
    def create_os_configure_runner(runner: CliRunner):
        return runner.invoke(
            get_fake_app(),
            [
                "--dry-run",
                "--verbose",
                "--auto-prompt",
                "single-board",
                "raspberry-pi",
                "node",
                "configure",
            ],
        )

    @staticmethod
    def create_network_configure_runner(runner: CliRunner):
        return runner.invoke(
            get_fake_app(),
            [
                "--dry-run",
                "--verbose",
                "--auto-prompt",
                "single-board",
                "raspberry-pi",
                "node",
                "network",
                f"--static-ip-address={ARG_STATIC_IP_ADDRESS}",
                f"--gw-ip-address={ARG_GW_IP_ADDRESS}",
                f"--dns-ip-address={ARG_DNS_IP_ADDRESS}",
            ],
        )

    @mock.patch(f"{RPI_NODE_MODULE_PATH}.configure_cmd.RPiOsConfigureCmd.run")
    def test_run_rpi_node_configure_cmd_with_args_success(self, run_call: mock.MagicMock) -> None:
        TestCliRunner.run(RaspberryPiNodeCliTestShould.create_os_configure_runner)
        Assertion.expect_exists(self, run_call, arg_name="ctx")
        Assertion.expect_exists(self, run_call, arg_name="args")

    @mock.patch(f"{RPI_NODE_MODULE_PATH}.configure_cmd.RPiOsConfigureCmd.run", side_effect=StepEvaluationFailure())
    def test_run_rpi_node_configure_cmd_managed_failure(self, run_call: mock.MagicMock) -> None:
        Assertion.expect_output(
            self,
            expected="StepEvaluationFailure",
            method_to_run=lambda: TestCliRunner.run(RaspberryPiNodeCliTestShould.create_os_configure_runner),
        )

    @mock.patch(f"{RPI_NODE_MODULE_PATH}.configure_cmd.RPiOsConfigureCmd.run", side_effect=Exception())
    def test_run_rpi_node_configure_cmd_unmanaged_failure(self, run_call: mock.MagicMock) -> None:
        Assertion.expect_raised_failure(
            self,
            ex_type=CliApplicationException,
            method_to_run=lambda: TestCliRunner.run(RaspberryPiNodeCliTestShould.create_os_configure_runner),
        )

    def test_e2e_run_rpi_node_configure_success(self) -> None:
        Assertion.expect_outputs(
            self,
            expected=[
                f"bash external/shell_scripts_lib/runner/ansible/ansible.sh",
                f"working_dir: {os.getcwd()}",
                "provisioner_single_board_plugin/raspberry_pi/node/playbooks/configure_os.yaml",
                "selected_host: DRY_RUN_RESPONSE ansible_host=DRY_RUN_RESPONSE ansible_user=DRY_RUN_RESPONSE ansible_password=DRY_RUN_RESPONSE",
                "ansible_var: host_name=DRY_RUN_RESPONSE",
                "ansible_tag: configure_remote_node",
                "ansible_tag: reboot",
            ],
            method_to_run=lambda: TestCliRunner.run(RaspberryPiNodeCliTestShould.create_os_configure_runner),
        )

    @mock.patch(f"{RPI_NODE_MODULE_PATH}.network_cmd.RPiNetworkConfigureCmd.run")
    def test_run_rpi_node_network_cmd_with_args_success(self, run_call: mock.MagicMock) -> None:
        TestCliRunner.run(RaspberryPiNodeCliTestShould.create_network_configure_runner)

        def assertion_callback(args):
            self.assertEqual(args.static_ip_address, ARG_STATIC_IP_ADDRESS)
            self.assertEqual(args.gw_ip_address, ARG_GW_IP_ADDRESS)
            self.assertEqual(args.dns_ip_address, ARG_DNS_IP_ADDRESS)

        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
        Assertion.expect_exists(self, run_call, arg_name="ctx")

    @mock.patch(f"{RPI_NODE_MODULE_PATH}.network_cmd.RPiNetworkConfigureCmd.run", side_effect=StepEvaluationFailure())
    def test_run_rpi_node_network_cmd_managed_failure(self, run_call: mock.MagicMock) -> None:
        Assertion.expect_output(
            self,
            expected="StepEvaluationFailure",
            method_to_run=lambda: TestCliRunner.run(RaspberryPiNodeCliTestShould.create_network_configure_runner),
        )

    @mock.patch(f"{RPI_NODE_MODULE_PATH}.network_cmd.RPiNetworkConfigureCmd.run", side_effect=Exception())
    def test_run_rpi_node_network_cmd_unmanaged_failure(self, run_call: mock.MagicMock) -> None:
        Assertion.expect_raised_failure(
            self,
            ex_type=CliApplicationException,
            method_to_run=lambda: TestCliRunner.run(RaspberryPiNodeCliTestShould.create_network_configure_runner),
        )

    def test_e2e_run_rpi_node_network_success(self) -> None:
        Assertion.expect_outputs(
            self,
            expected=[
                f"bash external/shell_scripts_lib/runner/ansible/ansible.sh",
                f"working_dir: {os.getcwd()}",
                "provisioner_single_board_plugin/raspberry_pi/node/playbooks/configure_network.yaml",
                "selected_host: DRY_RUN_RESPONSE ansible_host=DRY_RUN_RESPONSE",
                "ansible_var: host_name=DRY_RUN_RESPONSE",
                "ansible_var: static_ip=DRY_RUN_RESPONSE",
                "ansible_var: gateway_address=DRY_RUN_RESPONSE",
                "ansible_var: dns_address=DRY_RUN_RESPONSE",
                "ansible_tag: configure_rpi_network",
                "ansible_tag: define_static_ip",
                "ansible_tag: reboot",
            ],
            method_to_run=lambda: TestCliRunner.run(RaspberryPiNodeCliTestShould.create_network_configure_runner),
        )
