#!/usr/bin/env python3

import importlib
import os
import pathlib

from components.runtime.cli.entrypoint import EntryPoint
from loguru import logger

from provisioner_examples_plugin import main as example_plugin_main
from provisioner_shared.components.runtime.command.config.cli import append_config_cmd_to_cli
from provisioner_shared.components.runtime.command.plugins.cli import append_plugins_cmd_to_cli
from provisioner_shared.components.runtime.config.domain.config import ProvisionerConfig
from provisioner_shared.components.runtime.config.manager.config_manager import ConfigManager
from provisioner_shared.components.runtime.infra.context import Context
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators

PLUGIN_IMPORT_PATH = "main"

PROVISIONER_CONFIG_DEV_INTERNAL_PATH = (
    f"{pathlib.Path(__file__).parent.parent.parent.parent}/provisioner/provisioner/resources/config.yaml"
)
CONFIG_USER_PATH = os.path.expanduser("~/.config/provisioner/config.yaml")

"""
The --dry-run and --verbose flags aren't available on the pre-init phase
since logger is being set-up after Typer is initialized.
I've added pre Typer run env var to control the visiblity of components debug logs
such as config-loader, package-loader etc..
"""
ENV_VAR_ENABLE_PRE_INIT_DEBUG = "PROVISIONER_PRE_INIT_DEBUG"
debug_pre_init = os.getenv(key=ENV_VAR_ENABLE_PRE_INIT_DEBUG, default=False)

if not debug_pre_init:
    logger.remove()

ConfigManager.instance().load(PROVISIONER_CONFIG_DEV_INTERNAL_PATH, CONFIG_USER_PATH, ProvisionerConfig)

root_menu = EntryPoint.create_cli_menu()

try:
    logger.debug(f"Importing module {PLUGIN_IMPORT_PATH}")
    plugin_main_module = importlib.import_module(PLUGIN_IMPORT_PATH)
    logger.debug(f"Running module callback on {PLUGIN_IMPORT_PATH}")
    example_plugin_main.load_config()
    example_plugin_main.append_to_cli(root_menu)
except Exception as ex:
    err_msg = f"Failed to import module. import_path: {PLUGIN_IMPORT_PATH}, ex: {ex}"
    logger.error(err_msg)
    raise Exception(err_msg)

cols = CoreCollaborators(Context.create_empty())
append_config_cmd_to_cli(root_menu, cols=cols)
append_plugins_cmd_to_cli(root_menu, cols=cols)


# ==============
# ENTRY POINT
# To run from source:
#   - poetry run provisioner ...
# ==============
def main():
    root_menu()
