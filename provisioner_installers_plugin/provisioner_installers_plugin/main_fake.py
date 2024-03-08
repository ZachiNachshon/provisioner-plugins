#!/usr/bin/env python3

import traceback

from provisioner_features_lib.config.config_resolver import ConfigResolver
from provisioner_features_lib.remote.domain.config import RemoteConfig
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts
from provisioner_features_lib.remote.typer_remote_opts_fakes import *
from provisioner.cli.entrypoint import EntryPoint
from provisioner.domain.serialize import SerializationBase

from provisioner_installers_plugin.installer.domain.config import InstallerConfig
from provisioner_installers_plugin.installer.domain.config_fakes import (
    TestDataclassInstallerConfig,
)

FAKE_APP_TITLE = "Fake Utility Installer Test App"
FAKE_CONFIG_USER_PATH = "~/my/config.yaml"

fake_app = EntryPoint.create_typer(
    title=FAKE_APP_TITLE,
)


class FakeTestAppConfig(SerializationBase):

    remote: RemoteConfig = None
    installer_config: InstallerConfig = None

    def __init__(self, remote: RemoteConfig, installer_config: InstallerConfig) -> None:
        super().__init__({})
        self.remote = remote
        self.installer_config = installer_config

    def _try_parse_config(self, dict_obj: dict):
        pass

    def merge(self, other: "SerializationBase") -> "SerializationBase":
        return self


def generate_fake_config():
    fake_remote_config = TestDataRemoteOpts.create_fake_remote_opts()._remote_config
    TyperRemoteOpts.load(fake_remote_config)

    ConfigResolver.config = FakeTestAppConfig(
        remote=fake_remote_config,
        installer_config=TestDataclassInstallerConfig.create_fake_installer_config(),
    )


def register_remote_cli_args():
    from provisioner_features_lib.remote.typer_remote_opts_callback import (
        remote_args_callback,
    )

    remote_args_callback(
        environment=TEST_DATA_ENVIRONMENT,
        node_username=TEST_DATA_REMOTE_NODE_USERNAME_1,
        node_password=TEST_DATA_REMOTE_NODE_PASSWORD_1,
        ssh_private_key_file_path=TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH_1,
        ip_discovery_range=TEST_DATA_REMOTE_IP_DISCOVERY_RANGE,
    )


def register_module_cli_args():
    from provisioner_installers_plugin.main import append_to_cli

    append_to_cli(fake_app)


def get_fake_app():
    try:
        generate_fake_config()
        register_remote_cli_args()
        register_module_cli_args()
    except Exception as ex:
        print(f"Fake provisioner installer CLI commands failed to load. ex: {ex}, trace:\n{traceback.format_exc()}")

    return fake_app


def main():
    get_fake_app()()
