#!/usr/bin/env python3

import traceback

from provisioner_single_board_plugin.main import append_to_cli
from provisioner_single_board_plugin.src.config.domain.config import SINGLE_BOARD_PLUGIN_NAME, SingleBoardConfig
from provisioner_single_board_plugin.src.config.domain.config_fakes import (
    TestDataSingleBoardConfig,
)

from components.remote.remote_opts_fakes import *
from provisioner_shared.components.runtime.cli.entrypoint import EntryPoint
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager

FAKE_APP_TITLE = "Fake Single Board Plugin Test App"
FAKE_CONFIG_USER_PATH = "~/my/config.yaml"

fake_app = EntryPoint.create_cli_menu(
    title=FAKE_APP_TITLE,
)


def generate_fake_config():
    return TestDataSingleBoardConfig.create_fake_single_board_config()


def register_fake_config(fake_cfg: SingleBoardConfig):
    ConfigManager.instance().config = fake_cfg
    ConfigManager.instance().config.dict_obj = fake_cfg.__dict__
    ConfigManager.instance().config.dict_obj["plugins"] = {}
    ConfigManager.instance().config.dict_obj["plugins"][SINGLE_BOARD_PLUGIN_NAME] = fake_cfg


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
