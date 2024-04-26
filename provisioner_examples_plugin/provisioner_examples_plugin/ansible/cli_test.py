#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner.test_lib.assertions import Assertion
from typer.testing import CliRunner

from provisioner_examples_plugin.main_fake import get_fake_app

EXPECTED_USERNAME = "test-user"

HELLO_WORLD_COMMAND_PATH = "provisioner_examples_plugin.ansible.hello_world_cmd.HelloWorldCmd"

runner = CliRunner()


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_examples_plugin/ansible/cli_test.py
#
class AnsibleHelloCliTestShould(unittest.TestCase):
    @mock.patch(f"{HELLO_WORLD_COMMAND_PATH}.run")
    def test_cli_ansible_hello_cmd_with_args_success(self, run_call: mock.MagicMock) -> None:
        runner.invoke(
            get_fake_app(),
            ["--dry-run", "--verbose", "examples", "ansible", "hello", f"--username={EXPECTED_USERNAME}"],
        )

        def assertion_callback(args):
            self.assertEqual(EXPECTED_USERNAME, args.username)

        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
