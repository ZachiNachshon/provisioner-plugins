#!/usr/bin/env python3

from provisioner_features_lib.anchor.domain.config import AnchorConfig
from provisioner_features_lib.anchor.typer_anchor_opts import TyperAnchorOpts
from provisioner_features_lib.config.config_resolver import ConfigResolver
from provisioner_features_lib.remote.domain.config import RemoteConfig, RunEnvironment
from provisioner_features_lib.remote.typer_remote_opts import TyperRemoteOpts
from provisioner_features_lib.remote.typer_remote_opts_fakes import FakeTyperRemoteOpts
from python_core_lib.cli.entrypoint import EntryPoint
from python_core_lib.domain.serialize import SerializationBase

FAKE_APP_TITLE = "Fake Test App"

ANCHOR_GITHUB_ORGANIZATION = "test-organization"
ANCHOR_GITHUB_REPOSITORY = "test-repository"
ANCHOR_GITHUB_BRANCH = "test-branch"
ANCHOR_GITHUB_GITHUB_ACCESS_TOKEN = "test-access-token"

REMOTE_ENVIRONMENT = RunEnvironment.Local
REMOTE_NODE_USERNAME = "test-user"
REMOTE_NODE_PASSWORD = "test-pass"
REMOTE_SSH_PRIVATE_KEY_FILE_PATH = "test-ssh-private-key"
REMOTE_IP_DISCOVERY_RANGE = "1.1.1.1/32"

class FakeTestAppConfig(SerializationBase):

    remote: RemoteConfig = RemoteConfig()
    anchor: AnchorConfig = AnchorConfig()

    def __init__(self) -> None:
        super().__init__({})

    def _try_parse_config(self, dict_obj: dict):
        pass

    def merge(self, other: "SerializationBase") -> "SerializationBase":
        return self

fake_app = EntryPoint.create_typer(
    title=FAKE_APP_TITLE,
)

ConfigResolver.config = FakeTestAppConfig()

anchor_config: AnchorConfig = ConfigResolver.config.anchor
anchor_config.github.organization = ANCHOR_GITHUB_ORGANIZATION
anchor_config.github.repository = ANCHOR_GITHUB_REPOSITORY
anchor_config.github.branch = ANCHOR_GITHUB_BRANCH
anchor_config.github.github_access_token = ANCHOR_GITHUB_GITHUB_ACCESS_TOKEN

TyperAnchorOpts.anchor_config = anchor_config
TyperRemoteOpts.remote_config = ConfigResolver.config.remote

FakeTyperRemoteOpts.create(TyperRemoteOpts.remote_config)

from provisioner_features_lib.remote.typer_remote_opts_callback import remote_args_callback
remote_args_callback(
    environment = REMOTE_ENVIRONMENT,
    node_username = REMOTE_NODE_USERNAME,
    node_password = REMOTE_NODE_PASSWORD,
    ssh_private_key_file_path = REMOTE_SSH_PRIVATE_KEY_FILE_PATH,
    ip_discovery_range = REMOTE_IP_DISCOVERY_RANGE
)
