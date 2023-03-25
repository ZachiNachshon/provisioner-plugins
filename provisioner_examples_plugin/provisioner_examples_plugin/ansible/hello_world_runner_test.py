#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv

from provisioner_examples_plugin.ansible.hello_world_runner import (
    HelloWorldRunner,
    HelloWorldRunnerArgs,
)

ANSIBLE_HELLO_WORLD_RUNNER_PATH = "provisioner_examples_plugin.ansible.hello_world_runner.HelloWorldRunner"

EXPECTED_USERNAME = "test-user"
EXPECTED_ANSIBLE_PLAYBOOK_RELATIVE_PATH_FROM_MODULE = "provisioner_examples_plugin/ansible/playbooks/hello_world.yaml"

#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest provisioner_examples_plugin/anchor/anchor_cmd_test.py
#
class HelloWorldRunnerTestShould(unittest.TestCase):
    @mock.patch(f"{ANSIBLE_HELLO_WORLD_RUNNER_PATH}.run")
    def test_ansible_hello_runner_run_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        env = TestEnv.create()
        ctx = env.get_context()
        expected_remote_opts = CliRemoteOpts.maybe_get()

        def assertion_callback(args):
            self.assertEqual(expected_remote_opts, args.remote_opts)
            self.assertEqual(EXPECTED_USERNAME, args.username)
            self.assertEqual(
                args.ansible_playbook_relative_path_from_module, EXPECTED_ANSIBLE_PLAYBOOK_RELATIVE_PATH_FROM_MODULE
            )

        HelloWorldRunner().run(
            ctx=ctx,
            collaborators=env.get_collaborators(),
            args=HelloWorldRunnerArgs(
                username=EXPECTED_USERNAME,
                ansible_playbook_relative_path_from_module=EXPECTED_ANSIBLE_PLAYBOOK_RELATIVE_PATH_FROM_MODULE,
                remote_opts=expected_remote_opts,
            ),
        )

        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
        Assertion.expect_call_argument(self, run_call, arg_name="ctx", expected_value=env.get_context())
