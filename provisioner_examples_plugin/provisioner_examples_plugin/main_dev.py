#!/usr/bin/env python3

import importlib
import os

from loguru import logger
from provisioner.cli.entrypoint import EntryPoint
from provisioner.config.domain.config import ProvisionerConfig
from provisioner.config.manager.config_manager import ConfigManager

from provisioner_examples_plugin import main as example_plugin_main

PLUGIN_IMPORT_PATH = "provisioner_examples_plugin.main"

CONFIG_USER_PATH = os.path.expanduser("~/.config/provisioner/config.yaml")

"""
The --dry-run and --verbose flags aren't available on the pre-init phase
since logger is being set-up after Typer is initialized.
I've added pre Typer run env var to control the visiblity of components debug logs
such as config-loader, package-loader etc..
"""
ENV_VAR_ENABLE_PRE_INIT_DEBUG = "PROVISIONER_PRE_INIT_DEBUG"
ENV_VAR_LOCAL_DEV_MODE = "PROVISIONER_LOCAL_DEV"
debug_pre_init = os.getenv(key=ENV_VAR_ENABLE_PRE_INIT_DEBUG, default=False)

app = EntryPoint.create_typer(
    title="Provision Everything Anywhere (install plugins from https://zachinachshon.com/provisioner)",
    config_resolver_fn=lambda: ConfigManager.instance().load(
        example_plugin_main.CONFIG_INTERNAL_PATH, CONFIG_USER_PATH, ProvisionerConfig, debug=debug_pre_init
    ),
)

try:
    logger.debug(f"Importing module {PLUGIN_IMPORT_PATH}")
    plugin_main_module = importlib.import_module(PLUGIN_IMPORT_PATH)
    logger.debug(f"Running module callback on {PLUGIN_IMPORT_PATH}")
    example_plugin_main.load_config()
    example_plugin_main.append_to_cli(app)
except Exception as ex:
    logger.error(f"Failed to import module. import_path: {PLUGIN_IMPORT_PATH}, ex: {ex}")


# ==============
# ENTRY POINT
# To run from source:
#   - poetry run provisioner ...
# ==============
def main():
    app()
