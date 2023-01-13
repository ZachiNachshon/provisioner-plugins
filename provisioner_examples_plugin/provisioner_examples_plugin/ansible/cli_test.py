#!/usr/bin/env python3

import unittest
from unittest import mock

from typer.testing import CliRunner

from provisioner_examples_plugin.main_fake import get_fake_app

runner = CliRunner()

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_examples_plugin/ansible/cli_test.py
#
class AnsibleHelloCliTestShould(unittest.TestCase):
    @mock.patch("provisioner_examples_plugin.ansible.hello_world_cmd.HelloWorldCmd.run")
    def test_cli_ansible_hello_cmd_with_args_success(self, run_call: mock.MagicMock) -> None:
        expected_username = "test-user"

        result = runner.invoke(
            get_fake_app(),
            ["--dry-run", "--verbose", "examples", "ansible", "hello", f"--username={expected_username}"],
        )
        self.assertEqual(1, run_call.call_count)

        run_call_kwargs = run_call.call_args.kwargs
        ctx = run_call_kwargs["ctx"]
        call_args = run_call_kwargs["args"]

        self.assertIsNotNone(ctx)
        self.assertIsNotNone(call_args)
        self.assertEqual(call_args.username, expected_username)
