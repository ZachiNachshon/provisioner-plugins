#!/usr/bin/env python3

import traceback

from provisioner.cli.entrypoint import EntryPoint
from provisioner.config.manager.config_manager import ConfigManager
from provisioner.domain.serialize import SerializationBase
from provisioner_features_lib.remote.domain.config import RemoteConfig
from provisioner_features_lib.remote.typer_remote_opts_fakes import *
from provisioner_features_lib.vcs.domain.config import VersionControlConfig
from provisioner_features_lib.vcs.typer_vcs_opts_fakes import TestDataVersionControlOpts

from provisioner_examples_plugin.main import append_to_cli
from provisioner_examples_plugin.config.domain.config import ExamplesConfig
from provisioner_examples_plugin.config.domain.config_fakes import TestDataExamplesConfig

FAKE_APP_TITLE = "Fake Examples Plugin Test App"
FAKE_CONFIG_USER_PATH = "~/my/config.yaml"

fake_app = EntryPoint.create_typer(
    title=FAKE_APP_TITLE,
)


class FakeTestAppConfig(SerializationBase):

    remote: RemoteConfig = None
    vcs: VersionControlConfig = None
    hello_world: ExamplesConfig.HelloWorldConfig = None

    def __init__(self, dict_obj: dict) -> None:
        super().__init__(dict_obj)

    def _try_parse_config(self, dict_obj: dict):
        pass

    def merge(self, other: "SerializationBase") -> "SerializationBase":
        return self


def generate_fake_config():
    return TestDataExamplesConfig.create_fake_example_config()

def register_fake_config(fake_cfg: FakeTestAppConfig):
    ConfigManager.instance().config = fake_cfg
    ConfigManager.instance().config.dict_obj = fake_cfg.__dict__
    ConfigManager.instance().config.dict_obj["plugins"] = {}
    ConfigManager.instance().config.dict_obj["plugins"]["example-plugin"] = fake_cfg

def register_module_cli_args():
    append_to_cli(fake_app)

def get_fake_app():
    try:
        fake_cfg = generate_fake_config()
        register_fake_config(fake_cfg)
        register_module_cli_args()
    except Exception as ex:
        print(f"Fake provisioner example CLI commands failed to load. ex: {ex}, trace:\n{traceback.format_exc()}")

    return fake_app


def main():
    fake_app()
