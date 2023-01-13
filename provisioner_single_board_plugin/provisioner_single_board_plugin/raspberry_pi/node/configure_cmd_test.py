#!/usr/bin/env python3

import unittest
from unittest import SkipTest, mock

from python_core_lib.infra.context import Context
from python_core_lib.utils.os import MAC_OS, OsArch

from provisioner_single_board_plugin.raspberry_pi.node.configure_cmd import (
    RPiOsConfigureCmd,
    RPiOsConfigureCmdArgs,
)


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_single_board_plugin/raspberry_pi/node/configure_cmd/configure_test.py
#
class RPiOsConfigureTestShould(unittest.TestCase):
    @SkipTest
    @mock.patch("common.remote.remote_os_configure.RemoteMachineOsConfigureRunner.run")
    def test_configure_os_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        expected_username = "test-user"
        expected_password = "test-pass"
        expected_ip_discovery_range = "192.168.1.1/24"
        expected_ansible_playbook_configure_os = "rpi/os/playbooks/configure_os.yaml"

        args = RPiOsConfigureCmdArgs(
            node_username=expected_username,
            node_password=expected_password,
            ip_discovery_range=expected_ip_discovery_range,
        )

        runner = RPiOsConfigureCmd()
        runner.run(ctx=ctx, args=args)

        run_call_kwargs = run_call.call_args.kwargs
        ctx_call_arg = run_call_kwargs["ctx"]
        configure_os_call_args = run_call_kwargs["args"]

        self.assertEqual(ctx, ctx_call_arg)
        self.assertEqual(expected_username, configure_os_call_args.node_username)
        self.assertEqual(expected_password, configure_os_call_args.node_password)
        self.assertEqual(expected_ip_discovery_range, configure_os_call_args.ip_discovery_range)
        self.assertEqual(
            expected_ansible_playbook_configure_os, configure_os_call_args.ansible_playbook_path_configure_os
        )
