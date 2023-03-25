#!/usr/bin/env python3

import traceback

from provisioner_features_lib.anchor.domain.config import AnchorConfig
from provisioner_features_lib.anchor.typer_anchor_opts import TyperAnchorOpts
from provisioner_features_lib.anchor.typer_anchor_opts_fakes import TestDataAnchorOpts
from provisioner_features_lib.config.config_resolver import ConfigResolver
from provisioner_features_lib.remote.domain.config import RemoteConfig
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts
from provisioner_features_lib.remote.typer_remote_opts_fakes import *
from python_core_lib.cli.entrypoint import EntryPoint
from python_core_lib.domain.serialize import SerializationBase

from provisioner_examples_plugin.domain.config import DummyConfig
from provisioner_examples_plugin.domain.config_fakes import TestDataExamplesConfig

FAKE_APP_TITLE = "Fake Examples Plugin Test App"

fake_app = EntryPoint.create_typer(
    title=FAKE_APP_TITLE,
)


class FakeTestAppConfig(SerializationBase):

    remote: RemoteConfig = None
    anchor: AnchorConfig = None
    dummy: DummyConfig = None

    def __init__(self, remote: RemoteConfig, anchor: AnchorConfig, dummy: DummyConfig) -> None:
        super().__init__({})
        self.remote = remote
        self.anchor = anchor
        self.dummy = dummy

    def _try_parse_config(self, dict_obj: dict):
        pass

    def merge(self, other: "SerializationBase") -> "SerializationBase":
        return self


def generate_fake_config():
    fake_anchor_config = TestDataAnchorOpts.create_fake_anchor_opts().anchor_config
    TyperAnchorOpts.load(fake_anchor_config)

    fake_remote_config = TestDataRemoteOpts.create_fake_remote_opts().remote_config
    TyperRemoteOpts.load(fake_remote_config)

    ConfigResolver.config = FakeTestAppConfig(
        remote=fake_remote_config, anchor=fake_anchor_config, dummy=TestDataExamplesConfig.create_fake_dummy_config()
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
    from provisioner_examples_plugin.main import append_examples

    append_examples(fake_app)


def get_fake_app():
    try:
        generate_fake_config()
        register_remote_cli_args()
        register_module_cli_args()
    except Exception as ex:
        print(f"Fake provisioner example CLI commands failed to load. ex: {ex}, trace:\n{traceback.format_exc()}")

    return fake_app


def main():
    fake_app()
