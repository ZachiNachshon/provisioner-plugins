#!/usr/bin/env python3

import traceback

from components.remote.remote_opts_fakes import *

from provisioner_examples_plugin.main import append_to_cli
from provisioner_examples_plugin.src.config.domain.config import PLUGIN_NAME, ExamplesConfig
from provisioner_examples_plugin.src.config.domain.config_fakes import (
    TestDataExamplesConfig,
)
from provisioner_shared.components.runtime.cli.entrypoint import EntryPoint
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager

FAKE_APP_TITLE = "Fake Examples Plugin Test App"
FAKE_CONFIG_USER_PATH = "~/my/config.yaml"

root_menu = EntryPoint.create_cli_menu()


def generate_fake_config():
    return TestDataExamplesConfig.create_fake_example_config()


def register_fake_config(fake_cfg: ExamplesConfig):
    ConfigManager.instance().config = fake_cfg
    ConfigManager.instance().config.dict_obj = fake_cfg.__dict__
    ConfigManager.instance().config.dict_obj["plugins"] = {}
    ConfigManager.instance().config.dict_obj["plugins"][PLUGIN_NAME] = fake_cfg


def register_module_cli_args():
    append_to_cli(root_menu)


def get_fake_app():
    try:
        fake_cfg = generate_fake_config()
        register_fake_config(fake_cfg)
        register_module_cli_args()
    except Exception as ex:
        print(f"Fake provisioner example CLI commands failed to load. ex: {ex}, trace:\n{traceback.format_exc()}")

    return root_menu


def main():
    root_menu()
