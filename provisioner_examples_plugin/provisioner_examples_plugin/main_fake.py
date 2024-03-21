#!/usr/bin/env python3

import traceback

from provisioner.cli.entrypoint import EntryPoint
from provisioner.config.manager.config_manager import ConfigManager
from provisioner_features_lib.remote.typer_remote_opts_fakes import *

from provisioner_examples_plugin.config.domain.config import PLUGIN_NAME, ExamplesConfig
from provisioner_examples_plugin.config.domain.config_fakes import TestDataExamplesConfig
from provisioner_examples_plugin.main import append_to_cli

FAKE_APP_TITLE = "Fake Examples Plugin Test App"
FAKE_CONFIG_USER_PATH = "~/my/config.yaml"

fake_app = EntryPoint.create_typer(
    title=FAKE_APP_TITLE,
)


def generate_fake_config():
    return TestDataExamplesConfig.create_fake_example_config()


def register_fake_config(fake_cfg: ExamplesConfig):
    ConfigManager.instance().config = fake_cfg
    ConfigManager.instance().config.dict_obj = fake_cfg.__dict__
    ConfigManager.instance().config.dict_obj["plugins"] = {}
    ConfigManager.instance().config.dict_obj["plugins"][PLUGIN_NAME] = fake_cfg


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
