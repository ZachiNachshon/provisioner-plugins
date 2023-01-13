#!/usr/bin/env python3

import unittest
from unittest import mock
from provisioner_examples_plugin.ansible.hello_world_cmd import HelloWorldCmd, HelloWorldCmdArgs
from provisioner_features_lib.remote.typer_remote_opts import CliRemoteOpts
from python_core_lib.test_lib.test_env import TestEnv

#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest provisioner_examples_plugin/ansible/hello_world_cmd_test.py
#
class HelloWorldCmdTestShould(unittest.TestCase):

    env = TestEnv.create()

    @mock.patch("provisioner_examples_plugin.ansible.hello_world_runner.HelloWorldRunner.run")
    def test_ansible_hello_cmd_run_with_expected_arguments(self, run_call: mock.MagicMock) -> None:
        ctx = self.env.get_context()

        expected_username = "test-user"
        expected_ansible_playbook_relative_path_from_root = "provisioner_examples_plugin/ansible/playbooks/hello_world.yaml"
        expected_remote_opts = CliRemoteOpts.maybe_get()

        HelloWorldCmd().run(
            ctx=ctx, 
            args=HelloWorldCmdArgs(
                username=expected_username, 
                remote_opts=expected_remote_opts
            )
        )

        run_call_kwargs = run_call.call_args.kwargs
        ctx_call_arg = run_call_kwargs["ctx"]
        cmd_call_args = run_call_kwargs["args"]

        self.assertEqual(ctx, ctx_call_arg)
        self.assertEqual(expected_username, cmd_call_args.username)
        self.assertEqual(expected_ansible_playbook_relative_path_from_root, cmd_call_args.ansible_playbook_relative_path_from_root)
        self.assertEqual(expected_remote_opts.environment, cmd_call_args.remote_opts.environment)

