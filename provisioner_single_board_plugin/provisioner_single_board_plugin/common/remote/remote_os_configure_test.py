#!/usr/bin/env python3

import unittest

from python_core_lib.errors.cli_errors import MissingUtilityException
from python_core_lib.infra.context import Context
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv
from python_core_lib.utils.os import LINUX, MAC_OS, WINDOWS, OsArch

from provisioner_single_board_plugin.common.remote.remote_os_configure import (
    RemoteMachineOsConfigureArgs,
    RemoteMachineOsConfigureRunner,
)


# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_single_board_plugin/common/remote/remote_os_configure_test.py
#
class RemoteMachineConfigureTestShould(unittest.TestCase):
    def create_fake_configure_args(self) -> RemoteMachineOsConfigureArgs:
        return RemoteMachineOsConfigureArgs(
            node_username="test-user",
            node_password="test-password",
            ip_discovery_range="1.1.1.1/24",
            ansible_playbook_path_configure_os="/test/path/ansible/playbook.yaml",
        )

    def test_prerequisites_fail_missing_utility(self) -> None:
        env = TestEnv.create()
        env.collaborators.override_checks.checks.register_utility("docker", exist=False)

        runner = RemoteMachineOsConfigureRunner()
        Assertion.expect_failure(
            self, ex_type=MissingUtilityException, method_to_run=lambda: runner.prerequisites(ctx, cols.checks)
        )

    def test_prerequisites_darwin_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.checks.register_utility("docker")
        runner = RemoteMachineOsConfigureRunner()
        Assertion.expect_success(self, method_to_run=lambda: runner.prerequisites(ctx, cols.checks))

    def test_prerequisites_linux_success(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=LINUX, arch="test_arch", os_release="test_os_release"))

        cols = self.create_fake_collaborators(ctx)
        cols.checks.register_utility("docker")
        runner = RemoteMachineOsConfigureRunner()
        Assertion.expect_success(self, method_to_run=lambda: runner.prerequisites(ctx, cols.checks))

    def test_prerequisites_fail_on_os_not_supported(self) -> None:
        ctx = Context.create(os_arch=OsArch(os=WINDOWS, arch="test_arch", os_release="test_os_release"))

        runner = RemoteMachineOsConfigureRunner()
        Assertion.expect_failure(
            self, ex_type=NotImplementedError, method_to_run=lambda: runner.prerequisites(ctx, None)
        )

        ctx = Context.create(
            os_arch=OsArch(os="NOT-SUPPORTED", arch="test_arch", os_release="test_os_release"),
            verbose=False,
            dry_run=False,
        )
        runner = RemoteMachineOsConfigureRunner()
        Assertion.expect_failure(
            self, ex_type=NotImplementedError, method_to_run=lambda: runner.prerequisites(ctx, None)
        )
