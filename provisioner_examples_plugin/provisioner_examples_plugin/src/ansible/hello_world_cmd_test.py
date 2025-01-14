#!/usr/bin/env python3

import unittest
from unittest import mock

from components.remote.remote_opts_fakes import TestDataRemoteOpts

from provisioner_examples_plugin.src.ansible.hello_world_cmd import (
    HelloWorldCmd,
    HelloWorldCmdArgs,
)
from provisioner_shared.components.remote.domain.config import RunEnvironment
from provisioner_shared.components.runtime.test_lib.assertions import Assertion
from provisioner_shared.components.runtime.test_lib.test_env import TestEnv

ANSIBLE_HELLO_WORLD_RUNNER_PATH = "provisioner_examples_plugin.src.ansible.hello_world_runner.HelloWorldRunner"


#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest plugins/provisioner_examples_plugin/provisioner_examples_plugin/src/ansible/hello_world_cmd_test.py
#
class HelloWorldCmdTestShould(unittest.TestCase):

    env = TestEnv.create()

    @mock.patch(f"{ANSIBLE_HELLO_WORLD_RUNNER_PATH}.run")
    def test_ansible_hello_cmd_run_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        ctx = self.env.get_context()

        expected_username = "test-user"
        expected_remote_opts = TestDataRemoteOpts.create_fake_cli_remote_opts(environment=RunEnvironment.Remote)

        HelloWorldCmd().run(
            ctx=ctx,
            args=HelloWorldCmdArgs(username=expected_username, remote_opts=expected_remote_opts),
        )

        def assertion_callback(args):
            self.assertEqual(expected_username, args.username)
            self.assertEqual(expected_remote_opts.environment, args.remote_opts.environment)

        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
