#!/usr/bin/env python3

import unittest

import pytest

from provisioner.main import root_menu
from provisioner_shared.test_lib.cli_container import RemoteSSHContainer
from provisioner_shared.test_lib.test_cli_runner import TestCliRunner


# To run these directly from the terminal use:
#  ./run_tests.py plugins/provisioner_examples_plugin/provisioner_examples_plugin/src/ansible/hello_world_runner_e2e_test.py
#
@pytest.mark.e2e
class HelloWorldE2ETestShould(unittest.TestCase):

    # Run before each test
    @classmethod
    def setUpClass(cls):
        """Start the container once before any tests in this class."""
        # cls.container = RemoteSSHContainer(CoreCollaborators(Context.create_empty()), allow_logging=True)
        cls.container = RemoteSSHContainer()
        cls.container.start()

    # Stop after each test
    @classmethod
    def tearDownClass(cls):
        """Stop the container after all tests in this class have completed."""
        if cls.container:
            cls.container.stop()
            cls.container = None  # Ensure cleanup

    def test_e2e_examples_hello_world_command_run_remote_successfully(self):
        result = TestCliRunner.run(
            root_menu,
            [
                "examples",
                "ansible",
                "--environment",
                "Remote",
                "--connect-mode",
                "Flags",
                "--node-username",
                "pi",
                "--node-password",
                "raspberry",
                "--ip-address",
                "127.0.0.1",
                "--port",
                "2222",
                "--hostname",
                "test-node",
                "--verbosity",
                "Verbose",
                "hello",
                "--username",
                "RemoteTestUser",
                "-vy",
            ],
        )
        self.assertIn("Hello World, RemoteTestUser", result)

    def test_examples_hello_world_command_run_local_successfully(self):
        result = TestCliRunner.run(
            root_menu,
            [
                "examples",
                "ansible",
                "--environment",
                "Local",
                "--connect-mode",
                "Flags",
                "--node-username",
                "pi",
                "--node-password",
                "none",
                "--ip-address",
                "ansible_connection=local",
                "--hostname",
                "test-node",
                "--verbosity",
                "Verbose",
                "hello",
                "--username",
                "LocalTestUser",
                "-vy",
            ],
        )
        self.assertIn("Hello World, LocalTestUser", result)
