#!/usr/bin/env python3

import unittest
from unittest import mock

from provisioner_features_lib.remote.typer_remote_opts_fakes import TestDataRemoteOpts
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.test_lib.test_env import TestEnv
from python_core_lib.utils.os import MAC_OS, OsArch

from provisioner_installers_plugin.installer.cmd.installer_cmd import (
    UtilityInstallerCmd,
    UtilityInstallerCmdArgs,
)
from provisioner_installers_plugin.installer.domain.source import InstallSources
from provisioner_installers_plugin.installer.runner.installer_runner import (
    UtilityInstallerRunnerCmdArgs,
)
from provisioner_installers_plugin.installer.utilities import SupportedToolings

TEST_GITHUB_OWNER = "test-owner"
TEST_GITHUB_REPO = "test-repo"
TEST_GITHUB_RELEASE_NAME = "test-cli"
TEST_GITHUB_SUPPORTED_RELEASES = ["darwin_arm64", "linux_amd64"]
TEST_GITHUB_ACCESS_TOKEN = "top-secret"
TEST_GITHUB_RELEASE_VERSION = "v0.10.0"
TEST_GITHUB_RELEASE_FILENAME = f"{TEST_GITHUB_RELEASE_NAME}_v0.10.0_darwin_arm64.tar.gz"
TEST_RELEASE_BINARY_OS_ARCH = OsArch(os=MAC_OS, arch="arm64")

# To run as a single test target:
#  poetry run coverage run -m pytest provisioner_installers_plugin/installer/domain/source_test.py
#
class InstallSourcesTestShould(unittest.TestCase):

    env = TestEnv.create()

    def create_fake_github_source(self) -> InstallSources.GitHub:
        return InstallSources.GitHub(
            owner=TEST_GITHUB_OWNER,
            repo=TEST_GITHUB_REPO,
            supported_releases=TEST_GITHUB_SUPPORTED_RELEASES,
            github_access_token=TEST_GITHUB_ACCESS_TOKEN,
            release_name_resolver=lambda version, os, arch: f"{TEST_GITHUB_RELEASE_NAME}_{version}_{os}_{arch}.tar.gz",
        )

    def test_github_source_generate_binary_url_success(self) -> None:
        fake_github_src = self.create_fake_github_source()
        release_filename = fake_github_src.resolve_binary_release_name(TEST_RELEASE_BINARY_OS_ARCH, version=TEST_GITHUB_RELEASE_VERSION)
        self.assertEqual(TEST_GITHUB_RELEASE_FILENAME, release_filename)

    def test_github_source_os_arch_not_supported(self) -> None:
        fake_github_src = self.create_fake_github_source()
        url = fake_github_src.resolve_binary_release_name(OsArch(os=MAC_OS, arch="amd32"), version=TEST_GITHUB_RELEASE_VERSION)
        self.assertIsNone(url)
