#!/usr/bin/env python3

import unittest
from unittest import mock

from components.runtime.test_lib.test_cli_runner import TestCliRunner

from provisioner_examples_plugin.main_fake import get_fake_app
from provisioner_shared.components.runtime.test_lib.assertions import Assertion

EXPECTED_USERNAME = "test-user"

HELLO_WORLD_COMMAND_PATH = "provisioner_examples_plugin.src.ansible.hello_world_cmd.HelloWorldCmd"


# To run as a single test target:
#  poetry run coverage run -m pytest plugins/provisioner_examples_plugin/provisioner_examples_plugin/src/ansible/cli_test.py
#
class AnsibleHelloCliTestShould(unittest.TestCase):
    @mock.patch(f"{HELLO_WORLD_COMMAND_PATH}.run")
    def test_cli_ansible_hello_cmd_with_args_success(self, run_call: mock.MagicMock) -> None:
        TestCliRunner.run(
            get_fake_app(),
            [
                "--dry-run",
                "--verbose",
                "examples",
                "ansible",
                "hello",
                f"--username={EXPECTED_USERNAME}",
            ],
        )

        def assertion_callback(args):
            self.assertEqual(EXPECTED_USERNAME, args.username)

        Assertion.expect_call_arguments(self, run_call, arg_name="args", assertion_callable=assertion_callback)
