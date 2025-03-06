#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_examples_plugin.src.ansible.hello_world_cmd import (
    HelloWorldCmd,
    HelloWorldCmdArgs,
)
from provisioner_shared.components.remote.domain.config import RunEnvironment
from provisioner_shared.components.remote.remote_opts_fakes import TestDataRemoteOpts
from provisioner_shared.test_lib.assertions import Assertion
from provisioner_shared.test_lib.test_env import TestEnv

ANSIBLE_HELLO_WORLD_RUNNER_PATH = "provisioner_examples_plugin.src.ansible.hello_world_runner.HelloWorldRunner"


#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest plugins/provisioner_examples_plugin/provisioner_examples_plugin/src/ansible/hello_world_cmd_test.py
#
class HelloWorldCmdTestShould(unittest.TestCase):

    env = TestEnv.create()

    @mock.patch(f"{ANSIBLE_HELLO_WORLD_RUNNER_PATH}.run")
    def test_ansible_hello_cmd_to_runner_arguments(self, run_call: mock.MagicMock) -> None:
        ctx = self.env.get_context()
        expected_username = "test-user"
        expected_remote_opts = TestDataRemoteOpts.create_fake_cli_remote_opts(environment=RunEnvironment.Remote)

        def assertion_callback(args):
            self.assertEqual(expected_username, args.username)
            self.assertEqual(expected_remote_opts.get_environment(), args.remote_opts.get_environment())
            self.assertEqual(expected_remote_opts.get_connect_mode(), args.remote_opts.get_connect_mode())
            self.assertEqual(expected_remote_opts.get_remote_context(), args.remote_opts.get_remote_context())
            self.assertEqual(expected_remote_opts.get_config(), args.remote_opts.get_config())
            self.assertEqual(expected_remote_opts.get_conn_flags(), args.remote_opts.get_conn_flags())
            self.assertEqual(expected_remote_opts.get_scan_flags(), args.remote_opts.get_scan_flags())

        HelloWorldCmd().run(
            ctx=ctx,
            args=HelloWorldCmdArgs(username=expected_username, remote_opts=expected_remote_opts),
        )
        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
