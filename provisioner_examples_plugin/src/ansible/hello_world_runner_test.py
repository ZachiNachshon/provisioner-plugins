#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_examples_plugin.src.ansible.hello_world_runner import (
    HelloWorldRunner,
    HelloWorldRunnerArgs,
)
from provisioner_shared.components.remote.typer_remote_opts_fakes import TestDataRemoteOpts
from provisioner_shared.components.runtime.test_lib.assertions import Assertion
from provisioner_shared.components.runtime.test_lib.test_env import TestEnv

ANSIBLE_HELLO_WORLD_RUNNER_PATH = "provisioner_examples_plugin.src.ansible.hello_world_runner.HelloWorldRunner"

EXPECTED_USERNAME = "test-user"


#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest src/ansible/hello_world_runner_test.py
#
class HelloWorldRunnerTestShould(unittest.TestCase):
    @mock.patch(f"{ANSIBLE_HELLO_WORLD_RUNNER_PATH}.run")
    def test_ansible_hello_runner_run_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        ctx = env.get_context()
        expected_remote_opts = TestDataRemoteOpts.create_fake_cli_remote_opts()

        def assertion_callback(args):
            self.assertEqual(expected_remote_opts, args.remote_opts)
            self.assertEqual(EXPECTED_USERNAME, args.username)

        HelloWorldRunner().run(
            ctx=ctx,
            collaborators=env.get_collaborators(),
            args=HelloWorldRunnerArgs(
                username=EXPECTED_USERNAME,
                remote_opts=expected_remote_opts,
            ),
        )

        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
        Assertion.expect_call_argument(self, run_call, arg_name="ctx", expected_value=env.get_context())
