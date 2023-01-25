#!/usr/bin/env python3

from provisioner_features_lib.anchor.domain.config import AnchorConfig
from provisioner_features_lib.anchor.typer_anchor_opts import TyperAnchorOpts
from provisioner_features_lib.anchor.typer_anchor_opts_fakes import TestDataAnchorOpts
from provisioner_features_lib.config.config_resolver import ConfigResolver
from provisioner_features_lib.remote.domain.config import RemoteConfig
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts
from provisioner_features_lib.remote.typer_remote_opts_fakes import TestDataRemoteOpts
from python_core_lib.cli.entrypoint import EntryPoint
from python_core_lib.domain.serialize import SerializationBase

FAKE_APP_TITLE = "Fake Test App"

class FakeTestAppConfig(SerializationBase):
    
    remote: RemoteConfig = None
    anchor: AnchorConfig = None

    # TODO: Move those configs from provisioner into this module and create fakes for them
    #       Maybe it'll be wise to use a json which will be serialized??
    dummmy: DummyConfig = DummyConfig()
    rpi: RpiConfig = RpiConfig()

    def __init__(self, remote: RemoteConfig, anchor: AnchorConfig) -> None:
        super().__init__({})
        self.remote = remote
        self.anchor = anchor

    def _try_parse_config(self, dict_obj: dict):
        pass

    def merge(self, other: "SerializationBase") -> "SerializationBase":
        return self

fake_app = EntryPoint.create_typer(
    title=FAKE_APP_TITLE,
)

fake_anchor_config = TestDataAnchorOpts.create_fake_anchor_opts().anchor_config
TyperAnchorOpts.load(fake_anchor_config)

fake_remote_config = TestDataRemoteOpts.create_fake_remote_opts().remote_config
TyperRemoteOpts.load(fake_remote_config)

ConfigResolver.config = FakeTestAppConfig(remote=fake_remote_config, anchor=fake_anchor_config)

from provisioner_features_lib.remote.typer_remote_opts_callback import remote_args_callback
remote_args_callback(
    environment = TestDataRemoteOpts.TEST_DATA_ENVIRONMENT,
    node_username = TestDataRemoteOpts.TEST_DATA_REMOTE_NODE_USERNAME,
    node_password = TestDataRemoteOpts.TEST_DATA_REMOTE_NODE_PASSWORD,
    ssh_private_key_file_path = TestDataRemoteOpts.TEST_DATA_REMOTE_SSH_PRIVATE_KEY_FILE_PATH,
    ip_discovery_range = TestDataRemoteOpts.TEST_DATA_REMOTE_IP_DISCOVERY_RANGE
)
